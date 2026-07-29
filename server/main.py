from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Supplier lead times are a procurement attribute of the part, not of the demand
# forecast, so they live here rather than in demand_forecasts.json. Keeping them
# out of the forecast record also means all 32 inventory SKUs have a lead time,
# not just the ones that happen to be forecasted.
CATEGORY_LEAD_TIME_DAYS = {
    "Circuit Boards": 21,
    "Sensors": 14,
    "Actuators": 35,
    "Controllers": 10,
    "Power Supplies": 18
}

# Per-SKU exceptions: single-source suppliers, hazmat shipping, or local stock
SKU_LEAD_TIME_OVERRIDES = {
    "SRV-302": 45,
    "PSU-508": 30,
    "PRX-204": 7
}

DEFAULT_LEAD_TIME_DAYS = 14

# Trend multiplies restock urgency: rising demand is riskier to under-stock
TREND_WEIGHT = {"increasing": 1.3, "stable": 1.0, "decreasing": 0.7}

# Items already below their reorder point jump the queue
BELOW_REORDER_MULTIPLIER = 1.25

# Restocking orders submitted during this server session. Intentionally
# in-memory only and reset on restart, consistent with this demo's no-database
# design. Kept here rather than in mock_data.py, which only loads static JSON.
submitted_restocking_orders: List[dict] = []
_restocking_order_seq = 0

# User tasks created during this server session, same in-memory-only rationale.
# The client merges these with the mock tasks baked into useAuth.js, which use
# small integer ids - these use "task-N" strings so the two sets can never collide.
session_tasks: List[dict] = []
_task_seq = 0

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

def get_lead_time_days(item: dict) -> int:
    """Supplier lead time in days for an inventory item."""
    if item["sku"] in SKU_LEAD_TIME_OVERRIDES:
        return SKU_LEAD_TIME_OVERRIDES[item["sku"]]
    return CATEGORY_LEAD_TIME_DAYS.get(item["category"], DEFAULT_LEAD_TIME_DAYS)

def build_restocking_candidates(warehouse: Optional[str] = None,
                                category: Optional[str] = None) -> list:
    """Join demand forecasts to inventory and score each item's restock urgency.

    Only items whose forecasted demand exceeds what is on hand are candidates -
    everything else is already stocked well enough to skip.
    """
    inventory_by_sku = {item["sku"]: item for item in inventory_items}
    candidates = []

    for forecast in demand_forecasts:
        item = inventory_by_sku.get(forecast["item_sku"])
        if not item:
            # Forecast for a SKU we don't stock, so it can't be restocked
            continue

        # Reuse the shared filter helper so warehouse/category semantics
        # (including case-insensitive category matching) match every other endpoint
        if not apply_filters([item], warehouse, category):
            continue

        shortfall = forecast["forecasted_demand"] - item["quantity_on_hand"]
        if shortfall <= 0:
            continue

        below_reorder = item["quantity_on_hand"] < item["reorder_point"]
        weight = TREND_WEIGHT.get(forecast["trend"].lower(), 1.0)
        if below_reorder:
            weight *= BELOW_REORDER_MULTIPLIER

        candidates.append({
            "sku": item["sku"],
            "item_name": item["name"],
            "category": item["category"],
            "warehouse": item["warehouse"],
            "quantity_on_hand": item["quantity_on_hand"],
            "reorder_point": item["reorder_point"],
            "forecasted_demand": forecast["forecasted_demand"],
            "trend": forecast["trend"],
            "projected_shortfall": shortfall,
            "urgency_score": round(shortfall * weight, 2),
            "below_reorder_point": below_reorder,
            "unit_cost": item["unit_cost"],
            "lead_time_days": get_lead_time_days(item)
        })

    # Most urgent first. Ties break on cheaper unit cost (the budget stretches
    # further), then on SKU so the ordering is fully deterministic for tests.
    candidates.sort(key=lambda c: (-c["urgency_score"], c["unit_cost"], c["sku"]))
    return candidates

def allocate_budget(candidates: list, budget: float) -> tuple:
    """Greedily spend the budget down the urgency-ranked candidate list.

    This is urgency-greedy, not knapsack-optimal: it can fund one urgent
    expensive item and starve two cheaper ones with better combined coverage.
    That trade-off is deliberate - the ranking stays explainable to a buyer, and
    the editable quantity inputs in the UI are the manual override.
    """
    remaining = max(0.0, budget)
    allocated = 0.0

    for candidate in candidates:
        quantity = 0
        # Guard against a zero/negative unit cost, which would otherwise look
        # infinitely affordable
        if candidate["unit_cost"] > 0 and remaining >= candidate["unit_cost"]:
            affordable_units = int(remaining // candidate["unit_cost"])
            # Never order more than the projected gap, however much budget is left
            quantity = min(candidate["projected_shortfall"], affordable_units)

        line_cost = round(quantity * candidate["unit_cost"], 2)
        candidate["suggested_quantity"] = quantity
        candidate["suggested_cost"] = line_cost
        candidate["fully_covered"] = quantity == candidate["projected_shortfall"]

        # Round every step: unit costs carry 2 decimals and repeated
        # subtraction otherwise accumulates float drift
        remaining = round(remaining - line_cost, 2)
        allocated = round(allocated + line_cost, 2)

    return allocated, remaining

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class Task(BaseModel):
    # dueDate is camelCase to match the existing TasksModal.vue/useAuth.js contract,
    # which is already shipped. The snake_case convention used elsewhere in this API
    # would silently render a blank due date in the client.
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: str = "medium"
    dueDate: str

class RestockingRecommendation(BaseModel):
    sku: str
    item_name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    forecasted_demand: int
    trend: str
    projected_shortfall: int
    urgency_score: float
    below_reorder_point: bool
    unit_cost: float
    lead_time_days: int
    suggested_quantity: int
    suggested_cost: float
    fully_covered: bool

class RestockingRecommendationsResponse(BaseModel):
    budget: float
    recommendations: List[RestockingRecommendation]
    allocated_cost: float
    remaining_budget: float
    max_useful_budget: float
    cheapest_unit_cost: Optional[float] = None
    items_recommended: int
    total_candidates: int

class RestockingOrderLine(BaseModel):
    sku: str
    item_name: str
    quantity: int
    unit_cost: float
    line_cost: float
    lead_time_days: int

class CreateRestockingOrderLine(BaseModel):
    # Only sku and quantity: unit cost, name and lead time are re-derived
    # server-side so a client can never dictate what it pays
    sku: str
    quantity: int

class CreateRestockingOrderRequest(BaseModel):
    budget: Optional[float] = None
    items: List[CreateRestockingOrderLine]

class RestockingOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockingOrderLine]
    total_items: int
    total_units: int
    total_cost: float
    lead_time_days: int
    order_date: str
    expected_delivery: str
    status: str
    budget: Optional[float] = None

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/restocking/recommendations", response_model=RestockingRecommendationsResponse)
def get_restocking_recommendations(
    budget: float = Query(0, ge=0),
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get budget-fitted restocking recommendations derived from demand forecasts."""
    candidates = build_restocking_candidates(warehouse, category)
    allocated, remaining = allocate_budget(candidates, budget)

    # What it would cost to close every projected shortfall - drives the UI slider range
    max_useful = round(
        sum(c["projected_shortfall"] * c["unit_cost"] for c in candidates), 2
    )

    return {
        "budget": budget,
        "recommendations": candidates,
        "allocated_cost": allocated,
        "remaining_budget": remaining,
        "max_useful_budget": max_useful,
        "cheapest_unit_cost": min((c["unit_cost"] for c in candidates), default=None),
        "items_recommended": len([c for c in candidates if c["suggested_quantity"] > 0]),
        "total_candidates": len(candidates)
    }

@app.post("/api/restocking/orders", response_model=RestockingOrder, status_code=201)
def create_restocking_order(request: CreateRestockingOrderRequest):
    """Submit a restocking order for the current server session."""
    global _restocking_order_seq

    if not request.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    inventory_by_sku = {item["sku"]: item for item in inventory_items}
    lines = []
    total_cost = 0.0
    max_lead_time = 0

    for line in request.items:
        if line.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Quantity for {line.sku} must be greater than zero"
            )

        item = inventory_by_sku.get(line.sku)
        if not item:
            raise HTTPException(status_code=404, detail=f"Unknown SKU: {line.sku}")

        # Price and lead time come from inventory, never from the request body
        lead_time = get_lead_time_days(item)
        line_cost = round(line.quantity * item["unit_cost"], 2)

        lines.append({
            "sku": item["sku"],
            "item_name": item["name"],
            "quantity": line.quantity,
            "unit_cost": item["unit_cost"],
            "line_cost": line_cost,
            "lead_time_days": lead_time
        })
        total_cost = round(total_cost + line_cost, 2)
        max_lead_time = max(max_lead_time, lead_time)

    if request.budget and total_cost > request.budget:
        raise HTTPException(
            status_code=400,
            detail=f"Order total {total_cost} exceeds budget {request.budget}"
        )

    _restocking_order_seq += 1
    now = datetime.now()
    # The order is only complete once its slowest line arrives
    expected_delivery = now + timedelta(days=max_lead_time)

    order = {
        "id": f"rst-{_restocking_order_seq}",
        "order_number": f"RST-{now.year}-{_restocking_order_seq:04d}",
        "items": lines,
        "total_items": len(lines),
        "total_units": sum(line["quantity"] for line in lines),
        "total_cost": total_cost,
        "lead_time_days": max_lead_time,
        # Full ISO datetime rather than a bare date: the browser parses a
        # date-only string as UTC midnight, which renders a day early in
        # negative-offset timezones
        "order_date": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "expected_delivery": expected_delivery.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "Submitted",
        "budget": request.budget
    }

    submitted_restocking_orders.append(order)
    return order

@app.get("/api/restocking/orders", response_model=List[RestockingOrder])
def get_restocking_orders():
    """Get restocking orders submitted this session, newest first.

    Deliberately separate from /api/orders: restocking orders are outbound
    purchase commitments, while that list is inbound customer revenue feeding
    the dashboard, reports and spending calculations.
    """
    return list(reversed(submitted_restocking_orders))

def find_task(task_id: str) -> Optional[dict]:
    """Locate a session task by id, or None if it isn't one."""
    return next((task for task in session_tasks if task["id"] == task_id), None)

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get tasks created this session, newest first.

    The client merges these with the per-locale mock tasks in useAuth.js, so this
    list is empty on a fresh server and the modal still renders those.
    """
    return list(reversed(session_tasks))

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a task for the current server session."""
    global _task_seq

    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Task title cannot be empty")

    if request.priority not in ("high", "medium", "low"):
        raise HTTPException(
            status_code=400,
            detail="Priority must be one of: high, medium, low"
        )

    # The client sends a date input value, so reject anything that isn't a real
    # date before it reaches formatDueDate() and renders as "Invalid Date"
    try:
        datetime.strptime(request.dueDate, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="dueDate must be in YYYY-MM-DD format"
        )

    _task_seq += 1
    task = {
        "id": f"task-{_task_seq}",
        "title": title,
        "priority": request.priority,
        "dueDate": request.dueDate,
        "status": "pending"
    }

    session_tasks.append(task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed."""
    task = find_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task["status"] = "pending" if task["status"] == "completed" else "completed"
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a session task."""
    task = find_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    session_tasks.remove(task)
    return {"id": task_id, "deleted": True}

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
