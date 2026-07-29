"""
Tests for the restocking API endpoints (recommendations and submitted orders).
"""
import re
from datetime import datetime

import pytest

import main


@pytest.fixture(autouse=True)
def reset_restocking_orders():
    """Clear the session-scoped submitted-order store between tests.

    conftest builds the TestClient from a module-level app, so without this a
    POST in one test leaks into every later test and outcomes become
    order-dependent.
    """
    main.submitted_restocking_orders.clear()
    main._restocking_order_seq = 0
    yield
    main.submitted_restocking_orders.clear()
    main._restocking_order_seq = 0


def get_recommendations(client, **params):
    response = client.get("/api/restocking/recommendations", params=params)
    assert response.status_code == 200
    return response.json()


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_response_structure(self, client):
        """Test that the response carries every summary field."""
        data = get_recommendations(client, budget=20000)

        for key in ["budget", "recommendations", "allocated_cost", "remaining_budget",
                    "max_useful_budget", "cheapest_unit_cost", "items_recommended",
                    "total_candidates"]:
            assert key in data

        assert isinstance(data["recommendations"], list)
        assert data["total_candidates"] == len(data["recommendations"])

    def test_recommendation_item_structure(self, client):
        """Test that each recommendation row is fully populated."""
        data = get_recommendations(client, budget=20000)

        for row in data["recommendations"]:
            for key in ["sku", "item_name", "category", "warehouse", "quantity_on_hand",
                        "reorder_point", "forecasted_demand", "trend", "projected_shortfall",
                        "urgency_score", "below_reorder_point", "unit_cost", "lead_time_days",
                        "suggested_quantity", "suggested_cost", "fully_covered"]:
                assert key in row

    def test_all_candidates_have_positive_shortfall(self, client):
        """Test that only under-stocked items are recommended."""
        data = get_recommendations(client, budget=20000)

        assert data["total_candidates"] > 0
        for row in data["recommendations"]:
            assert row["projected_shortfall"] > 0
            assert row["forecasted_demand"] > row["quantity_on_hand"]

    def test_sorted_by_urgency_descending(self, client):
        """Test that the most urgent item comes first."""
        data = get_recommendations(client, budget=20000)
        scores = [row["urgency_score"] for row in data["recommendations"]]

        assert scores == sorted(scores, reverse=True)

    def test_tie_break_prefers_cheaper_unit_cost(self, client):
        """Test that equal urgency scores are ordered cheapest-first."""
        data = get_recommendations(client, budget=0)
        rows = data["recommendations"]

        by_sku = {row["sku"]: index for index, row in enumerate(rows)}

        # PSU-504, PSU-503 and HMD-202 all score 65.0 with unit costs
        # 38.25 < 45.75 < 125.00
        assert by_sku["PSU-504"] < by_sku["PSU-503"] < by_sku["HMD-202"]

    def test_below_reorder_items_get_urgency_boost(self, client):
        """Test that items under their reorder point are ranked up."""
        data = get_recommendations(client, budget=0)

        boosted = [row for row in data["recommendations"] if row["below_reorder_point"]]
        assert boosted, "Expected at least one below-reorder-point candidate"

        for row in boosted:
            base = row["projected_shortfall"] * main.TREND_WEIGHT[row["trend"].lower()]
            assert row["urgency_score"] > base

    def test_zero_budget_allocates_nothing(self, client):
        """Test that a zero budget still lists candidates but funds none."""
        data = get_recommendations(client, budget=0)

        assert data["total_candidates"] > 0
        assert data["items_recommended"] == 0
        assert data["allocated_cost"] == 0
        assert data["remaining_budget"] == 0
        assert all(row["suggested_quantity"] == 0 for row in data["recommendations"])

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget fails validation."""
        response = client.get("/api/restocking/recommendations", params={"budget": -5})
        assert response.status_code == 422

    def test_budget_is_never_exceeded(self, client):
        """Test that allocation stays within budget at several sizes."""
        for budget in [500, 5000, 20000, 100000]:
            data = get_recommendations(client, budget=budget)
            assert data["allocated_cost"] <= budget
            assert data["allocated_cost"] + data["remaining_budget"] == pytest.approx(budget)

    def test_quantity_never_exceeds_shortfall(self, client):
        """Test that no item is over-ordered, however large the budget."""
        data = get_recommendations(client, budget=10_000_000)

        for row in data["recommendations"]:
            assert row["suggested_quantity"] <= row["projected_shortfall"]

    def test_large_budget_covers_every_shortfall(self, client):
        """Test that a budget above max_useful_budget fully covers every item."""
        data = get_recommendations(client, budget=1_000_000)

        assert all(row["fully_covered"] for row in data["recommendations"])
        assert data["allocated_cost"] == pytest.approx(data["max_useful_budget"])
        assert data["items_recommended"] == data["total_candidates"]

    def test_partial_lot_allocation(self, client):
        """Test that a mid-range budget buys whole units of a partially funded item."""
        data = get_recommendations(client, budget=20000)

        partial = [row for row in data["recommendations"]
                   if 0 < row["suggested_quantity"] < row["projected_shortfall"]]

        assert partial, "Expected at least one partially funded item"
        for row in partial:
            assert not row["fully_covered"]
            # Whole units only, never a fractional order
            assert row["suggested_quantity"] == int(row["suggested_quantity"])

    def test_suggested_cost_matches_quantity(self, client):
        """Test that each line cost equals quantity times unit cost."""
        data = get_recommendations(client, budget=20000)

        for row in data["recommendations"]:
            expected = row["suggested_quantity"] * row["unit_cost"]
            assert row["suggested_cost"] == pytest.approx(expected, abs=0.01)

    def test_allocated_cost_matches_line_sum(self, client):
        """Test that the summary total equals the sum of the lines."""
        data = get_recommendations(client, budget=20000)
        line_sum = sum(row["suggested_cost"] for row in data["recommendations"])

        assert data["allocated_cost"] == pytest.approx(line_sum, abs=0.01)

    def test_cheapest_unit_cost_is_accurate(self, client):
        """Test that cheapest_unit_cost reflects the candidate list."""
        data = get_recommendations(client, budget=0)
        assert data["cheapest_unit_cost"] == min(r["unit_cost"] for r in data["recommendations"])

    def test_filter_by_warehouse(self, client):
        """Test that the warehouse filter narrows the candidate list."""
        unfiltered = get_recommendations(client, budget=50000)
        tokyo = get_recommendations(client, budget=50000, warehouse="Tokyo")

        assert tokyo["total_candidates"] > 0
        assert tokyo["total_candidates"] < unfiltered["total_candidates"]
        assert tokyo["max_useful_budget"] < unfiltered["max_useful_budget"]
        assert all(row["warehouse"] == "Tokyo" for row in tokyo["recommendations"])

    def test_filter_by_category_is_case_insensitive(self, client):
        """Test that the category filter matches regardless of case."""
        lower = get_recommendations(client, budget=50000, category="circuit boards")
        upper = get_recommendations(client, budget=50000, category="Circuit Boards")

        assert lower["total_candidates"] > 0
        assert lower["total_candidates"] == upper["total_candidates"]
        assert all(row["category"] == "Circuit Boards" for row in lower["recommendations"])

    def test_combined_filters(self, client):
        """Test that warehouse and category filters apply together."""
        data = get_recommendations(
            client, budget=50000, warehouse="Tokyo", category="power supplies"
        )

        for row in data["recommendations"]:
            assert row["warehouse"] == "Tokyo"
            assert row["category"] == "Power Supplies"

    def test_all_filter_value_is_noop(self, client):
        """Test that the 'all' sentinel does not filter anything out."""
        unfiltered = get_recommendations(client, budget=50000)
        explicit = get_recommendations(client, budget=50000, warehouse="all", category="all")

        assert explicit["total_candidates"] == unfiltered["total_candidates"]

    def test_lead_times_are_positive(self, client):
        """Test that every candidate carries a usable supplier lead time."""
        data = get_recommendations(client, budget=0)

        for row in data["recommendations"]:
            assert row["lead_time_days"] > 0


class TestRestockingOrderCreation:
    """Test suite for POST /api/restocking/orders."""

    def test_create_order_success(self, client):
        """Test that a valid order is created."""
        response = client.post("/api/restocking/orders", json={
            "budget": 50000,
            "items": [{"sku": "MCU-401", "quantity": 10}]
        })

        assert response.status_code == 201
        order = response.json()

        assert re.match(r"^RST-\d{4}-\d{4}$", order["order_number"])
        assert order["status"] == "Submitted"
        assert order["total_items"] == 1
        assert order["total_units"] == 10
        assert order["total_cost"] == pytest.approx(10 * 8.25)

    def test_order_number_increments(self, client):
        """Test that order numbers are sequential within a session."""
        payload = {"items": [{"sku": "MCU-401", "quantity": 1}]}

        first = client.post("/api/restocking/orders", json=payload).json()
        second = client.post("/api/restocking/orders", json=payload).json()

        year = datetime.now().year
        assert first["order_number"] == f"RST-{year}-0001"
        assert second["order_number"] == f"RST-{year}-0002"

    def test_server_derives_unit_cost(self, client):
        """Test that pricing comes from inventory, not the request body."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "SRV-301", "quantity": 2}]
        })

        line = response.json()["items"][0]
        assert line["unit_cost"] == 445.0
        assert line["item_name"] == "Micro Servo Motor"
        assert line["line_cost"] == pytest.approx(890.0)

    def test_lead_time_is_max_across_lines(self, client):
        """Test that the order completes only when its slowest line arrives."""
        response = client.post("/api/restocking/orders", json={
            "items": [
                {"sku": "MCU-401", "quantity": 5},   # Controllers, 10 days
                {"sku": "SRV-301", "quantity": 5}    # Actuators, 35 days
            ]
        })

        assert response.json()["lead_time_days"] == 35

    def test_sku_lead_time_override_applies(self, client):
        """Test that per-SKU lead time overrides beat the category default."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "PRX-204", "quantity": 1}]
        })

        # Sensors default to 14 days, but PRX-204 is overridden to 7
        assert response.json()["items"][0]["lead_time_days"] == 7

    def test_expected_delivery_matches_lead_time(self, client):
        """Test that expected delivery is order date plus lead time."""
        order = client.post("/api/restocking/orders", json={
            "items": [{"sku": "SRV-301", "quantity": 1}]
        }).json()

        ordered = datetime.fromisoformat(order["order_date"])
        delivery = datetime.fromisoformat(order["expected_delivery"])

        assert (delivery - ordered).days == order["lead_time_days"]

    def test_dates_are_full_iso_datetimes(self, client):
        """Test that dates carry a time component.

        A bare YYYY-MM-DD string is parsed as UTC midnight by the browser and
        renders a day early in negative-offset timezones.
        """
        order = client.post("/api/restocking/orders", json={
            "items": [{"sku": "MCU-401", "quantity": 1}]
        }).json()

        assert "T" in order["order_date"]
        assert "T" in order["expected_delivery"]

    def test_total_cost_sums_all_lines(self, client):
        """Test that the order total equals the sum of its lines."""
        order = client.post("/api/restocking/orders", json={
            "items": [
                {"sku": "MCU-401", "quantity": 10},
                {"sku": "PCB-001", "quantity": 4}
            ]
        }).json()

        assert order["total_items"] == 2
        assert order["total_units"] == 14
        assert order["total_cost"] == pytest.approx(sum(l["line_cost"] for l in order["items"]))

    def test_empty_items_rejected(self, client):
        """Test that an order with no lines is rejected."""
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 400

    def test_zero_quantity_rejected(self, client):
        """Test that a zero quantity line is rejected."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "MCU-401", "quantity": 0}]
        })
        assert response.status_code == 400

    def test_negative_quantity_rejected(self, client):
        """Test that a negative quantity line is rejected."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "MCU-401", "quantity": -5}]
        })
        assert response.status_code == 400

    def test_unknown_sku_rejected(self, client):
        """Test that an unstocked SKU returns 404."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "NOPE-999", "quantity": 5}]
        })
        assert response.status_code == 404

    def test_exceeding_budget_rejected(self, client):
        """Test that an order over its stated budget is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 10,
            "items": [{"sku": "SRV-302", "quantity": 5}]
        })
        assert response.status_code == 400

    def test_omitted_budget_skips_validation(self, client):
        """Test that an order without a budget is accepted."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "SRV-302", "quantity": 5}]
        })

        assert response.status_code == 201
        assert response.json()["budget"] is None

    def test_failed_order_is_not_stored(self, client):
        """Test that a rejected order leaves no trace."""
        client.post("/api/restocking/orders", json={
            "items": [{"sku": "NOPE-999", "quantity": 1}]
        })

        assert client.get("/api/restocking/orders").json() == []


class TestRestockingOrdersList:
    """Test suite for GET /api/restocking/orders."""

    def test_empty_initially(self, client):
        """Test that no orders exist at the start of a session."""
        response = client.get("/api/restocking/orders")

        assert response.status_code == 200
        assert response.json() == []

    def test_submitted_order_appears(self, client):
        """Test that a submitted order is listed."""
        created = client.post("/api/restocking/orders", json={
            "items": [{"sku": "MCU-401", "quantity": 3}]
        }).json()

        listed = client.get("/api/restocking/orders").json()

        assert len(listed) == 1
        assert listed[0]["order_number"] == created["order_number"]

    def test_orders_are_newest_first(self, client):
        """Test that the most recent order is listed first."""
        payload = {"items": [{"sku": "MCU-401", "quantity": 1}]}
        client.post("/api/restocking/orders", json=payload)
        second = client.post("/api/restocking/orders", json=payload).json()

        listed = client.get("/api/restocking/orders").json()

        assert len(listed) == 2
        assert listed[0]["order_number"] == second["order_number"]

    def test_restocking_orders_do_not_pollute_orders_endpoint(self, client):
        """Test that restocking orders stay out of customer order revenue.

        Restocking orders are outbound purchase commitments. Leaking them into
        /api/orders would corrupt the dashboard, quarterly reports, monthly
        trends and the finance revenue-vs-cost charts, which all iterate that
        same list.
        """
        orders_before = len(client.get("/api/orders").json())
        summary_before = client.get("/api/dashboard/summary").json()

        client.post("/api/restocking/orders", json={
            "items": [{"sku": "SRV-302", "quantity": 50}]
        })

        assert len(client.get("/api/orders").json()) == orders_before
        assert client.get("/api/dashboard/summary").json() == summary_before

    def test_restocking_orders_do_not_pollute_reports(self, client):
        """Test that quarterly and monthly report figures are unaffected."""
        quarterly_before = client.get("/api/reports/quarterly").json()
        monthly_before = client.get("/api/reports/monthly-trends").json()

        client.post("/api/restocking/orders", json={
            "items": [{"sku": "SRV-301", "quantity": 20}]
        })

        assert client.get("/api/reports/quarterly").json() == quarterly_before
        assert client.get("/api/reports/monthly-trends").json() == monthly_before
