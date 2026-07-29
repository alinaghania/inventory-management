export default {
  // Navigation
  nav: {
    overview: 'Overview',
    inventory: 'Inventory',
    orders: 'Orders',
    finance: 'Finance',
    demandForecast: 'Demand Forecast',
    restocking: 'Restocking',
    reports: 'Reports',
    companyName: 'Catalyst Components',
    subtitle: 'Inventory Management System'
  },

  // Dashboard
  dashboard: {
    title: 'Overview',
    kpi: {
      title: 'Key Performance Indicators',
      inventoryTurnover: 'Inventory Turnover Rate',
      ordersFulfilled: 'Orders Fulfilled',
      orderFillRate: 'Order Fill Rate',
      revenue: 'Revenue (Orders)',
      revenueYTD: 'Revenue (Orders) YTD',
      revenueMTD: 'Revenue (Orders) MTD',
      avgProcessingTime: 'Avg Processing Time (Days)',
      goal: 'Goal'
    },
    summary: {
      title: 'Summary'
    },
    orderHealth: {
      title: 'Order Health',
      totalOrders: 'Total Orders',
      revenue: 'Revenue',
      avgOrderValue: 'Avg Order Value',
      onTimeRate: 'On-Time Rate',
      avgFulfillmentDays: 'Avg Fulfillment (Days)',
      total: 'Total'
    },
    ordersByMonth: {
      title: 'Orders by Month'
    },
    inventoryValue: {
      title: 'Inventory Value by Category'
    },
    inventoryShortages: {
      title: 'Inventory Shortages',
      noShortages: 'No inventory shortages - all orders can be fulfilled!',
      noData: 'No inventory data for selected filters',
      orderId: 'Order ID',
      sku: 'SKU',
      itemName: 'Item Name',
      quantityNeeded: 'Quantity Needed',
      quantityAvailable: 'Quantity Available',
      shortage: 'Shortage',
      daysDelayed: 'Days Delayed',
      priority: 'Priority',
      actions: 'Actions',
      unitsShort: 'units short',
      days: 'days'
    },
    topProducts: {
      title: 'Top Products by Revenue',
      sku: 'SKU',
      product: 'Product',
      category: 'Category',
      warehouse: 'Warehouse',
      stockStatus: 'Stock Status',
      revenue: 'Revenue',
      unitsOrdered: 'Units Ordered',
      firstOrder: 'First Order',
      inStock: 'In Stock',
      lowStock: 'Low Stock'
    }
  },

  // Inventory
  inventory: {
    title: 'Inventory',
    description: 'Track and manage all inventory items',
    stockLevels: 'Stock Levels',
    skus: 'SKUs',
    searchPlaceholder: 'Search by item name...',
    clearSearch: 'Clear search',
    totalItems: 'Total Items',
    totalValue: 'Total Value',
    lowStockItems: 'Low Stock Items',
    warehouses: 'Warehouses',
    table: {
      sku: 'SKU',
      itemName: 'Item Name',
      name: 'Name',
      category: 'Category',
      warehouse: 'Warehouse',
      quantity: 'Quantity',
      quantityOnHand: 'Quantity on Hand',
      reorderPoint: 'Reorder Point',
      unitCost: 'Unit Cost',
      unitPrice: 'Unit Price',
      totalValue: 'Total Value',
      location: 'Location',
      status: 'Status'
    }
  },

  // Orders
  orders: {
    title: 'Orders',
    description: 'View and manage customer orders',
    allOrders: 'All Orders',
    submittedOrders: 'Submitted Restocking Orders',
    totalOrders: 'Total Orders',
    totalRevenue: 'Total Revenue',
    avgOrderValue: 'Avg Order Value',
    onTimeDelivery: 'On-Time Delivery',
    itemsCount: '{count} items',
    quantity: 'Qty',
    table: {
      orderNumber: 'Order Number',
      orderId: 'Order ID',
      orderDate: 'Order Date',
      date: 'Date',
      customer: 'Customer',
      category: 'Category',
      warehouse: 'Warehouse',
      items: 'Items',
      value: 'Value',
      totalValue: 'Total Value',
      totalCost: 'Total Cost',
      leadTime: 'Lead Time',
      status: 'Status',
      expectedDelivery: 'Expected Delivery',
      actualDelivery: 'Actual Delivery'
    }
  },

  // Restocking
  restocking: {
    title: 'Restocking',
    description: 'Plan budget-driven restocking from demand forecasts',
    budgetTitle: 'Available Budget',
    budgetQuestion: 'If I only have {budget} to spend this cycle, what should I buy?',
    budgetHelp: 'Drag to set how much you can spend this cycle',
    budgetUsed: 'Budget Used',
    budgetRemaining: 'Remaining',
    overBudget: 'Over budget',
    recommendations: 'Recommended Restock',
    noRecommendations: 'No restocking needed for the current filters',
    increaseBudget: 'Increase the budget to at least {amount} to order the cheapest item',
    itemsRecommended: '{count} of {total} items funded',
    placeOrder: 'Place Order',
    placingOrder: 'Placing order...',
    orderPlaced: 'Restocking order {orderNumber} submitted',
    orderFailed: 'Failed to place order: {message}',
    selectAll: 'Select All',
    clearAll: 'Clear All',
    daysUnit: '{count} days',
    totalUnits: 'Total Units',
    totalCost: 'Total Cost',
    belowReorder: 'Below reorder point',
    table: {
      include: 'Include',
      sku: 'SKU',
      itemName: 'Item Name',
      category: 'Category',
      warehouse: 'Warehouse',
      onHand: 'On Hand',
      forecast: 'Forecast',
      shortfall: 'Shortfall',
      trend: 'Trend',
      unitCost: 'Unit Cost',
      leadTime: 'Lead Time',
      quantity: 'Order Qty',
      lineCost: 'Line Cost'
    }
  },

  // Finance/Spending
  finance: {
    title: 'Finance Dashboard',
    description: 'Track revenue, costs, and financial performance',
    totalRevenue: 'Total Revenue',
    totalCosts: 'Total Costs',
    netProfit: 'Net Profit',
    avgOrderValue: 'Avg Order Value',
    fromOrders: 'From {count} orders',
    costBreakdown: 'Procurement + Operational + Labor + Overhead',
    margin: 'margin',
    perOrderRevenue: 'Per order revenue',
    revenueVsCosts: {
      title: 'Monthly Revenue vs Costs',
      revenue: 'Revenue',
      costs: 'Total Costs'
    },
    monthlyCostFlow: {
      title: 'Monthly Cost Flow',
      procurement: 'Procurement',
      operational: 'Operational',
      labor: 'Labor',
      overhead: 'Overhead'
    },
    categorySpending: {
      title: 'Spending by Category',
      ofTotal: 'of total'
    },
    transactions: {
      title: 'Recent Transactions',
      id: 'ID',
      description: 'Description',
      vendor: 'Vendor',
      date: 'Date',
      amount: 'Amount'
    }
  },

  // Demand Forecast
  demand: {
    title: 'Demand Forecast',
    description: 'Analyze demand trends and forecasts',
    increasingDemand: 'Increasing Demand',
    stableDemand: 'Stable Demand',
    decreasingDemand: 'Decreasing Demand',
    itemsCount: '{count} items',
    more: 'more...',
    demandForecasts: 'Demand Forecasts',
    table: {
      sku: 'SKU',
      itemName: 'Item Name',
      currentDemand: 'Current Demand',
      forecastedDemand: 'Forecasted Demand',
      change: 'Change',
      trend: 'Trend',
      period: 'Period'
    }
  },

  // Reports
  reports: {
    title: 'Performance Reports',
    description: 'View quarterly performance metrics and monthly trends',
    loading: 'Loading reports...',
    loadError: 'Failed to load reports: {message}',
    emptyState: 'No orders match the current filters. Adjust or reset the filters to see reports.',
    notAvailable: 'N/A',
    // The API returns quarter codes as "Q1-2025"; these templates reorder the
    // parts per locale (English leads with the quarter, Japanese with the year)
    quarterFormat: 'Q{quarter} {year}',
    monthFormat: '{month} {year}',
    quarterly: {
      title: 'Quarterly Performance',
      quarter: 'Quarter',
      totalOrders: 'Total Orders',
      totalRevenue: 'Total Revenue',
      avgOrderValue: 'Avg Order Value',
      fulfillmentRate: 'Fulfillment Rate'
    },
    monthlyTrend: {
      title: 'Monthly Revenue Trend'
    },
    monthOverMonth: {
      title: 'Month-over-Month Analysis',
      month: 'Month',
      orders: 'Orders',
      revenue: 'Revenue',
      change: 'Change',
      growthRate: 'Growth Rate'
    },
    stats: {
      totalRevenueYtd: 'Total Revenue (YTD)',
      // "YTD" only holds with no filters active; under a month or warehouse
      // filter these totals cover the selected slice instead
      totalRevenueFiltered: 'Total Revenue (Filtered)',
      avgMonthlyRevenue: 'Avg Monthly Revenue',
      totalOrdersYtd: 'Total Orders (YTD)',
      totalOrdersFiltered: 'Total Orders (Filtered)',
      bestQuarter: 'Best Performing Quarter'
    }
  },

  // Filters
  filters: {
    timePeriod: 'Time Period',
    location: 'Location',
    category: 'Category',
    orderStatus: 'Order Status',
    all: 'All',
    allMonths: 'All Months',
    resetAll: 'Reset all filters'
  },

  // Statuses
  status: {
    delivered: 'Delivered',
    shipped: 'Shipped',
    processing: 'Processing',
    backordered: 'Backordered',
    submitted: 'Submitted',
    inStock: 'In Stock',
    lowStock: 'Low Stock',
    adequate: 'Adequate'
  },

  // Trends
  trends: {
    increasing: 'increasing',
    stable: 'stable',
    decreasing: 'decreasing'
  },

  // Priority
  priority: {
    high: 'High',
    medium: 'Medium',
    low: 'Low'
  },

  // Categories
  categories: {
    circuitBoards: 'Circuit Boards',
    sensors: 'Sensors',
    actuators: 'Actuators',
    controllers: 'Controllers',
    powerSupplies: 'Power Supplies'
  },

  // Spending Categories
  spendingCategories: {
    rawMaterials: 'Raw Materials',
    components: 'Components',
    equipment: 'Equipment',
    consumables: 'Consumables'
  },

  // Warehouses
  warehouses: {
    sanFrancisco: 'San Francisco',
    london: 'London',
    tokyo: 'Tokyo'
  },

  // Months
  months: {
    jan: 'Jan',
    feb: 'Feb',
    mar: 'Mar',
    apr: 'Apr',
    may: 'May',
    jun: 'Jun',
    jul: 'Jul',
    aug: 'Aug',
    sep: 'Sep',
    oct: 'Oct',
    nov: 'Nov',
    dec: 'Dec',
    january: 'January',
    february: 'February',
    march: 'March',
    april: 'April',
    june: 'June',
    july: 'July',
    august: 'August',
    september: 'September',
    october: 'October',
    november: 'November',
    december: 'December'
  },

  // Profile Menu
  profile: {
    profileDetails: 'Profile Details',
    myTasks: 'My Tasks',
    logout: 'Logout'
  },

  // Profile Details Modal
  profileDetails: {
    title: 'Profile Details',
    email: 'Email',
    department: 'Department',
    location: 'Location',
    phone: 'Phone',
    joinDate: 'Join Date',
    employeeId: 'Employee ID',
    close: 'Close'
  },

  // Tasks Modal
  tasks: {
    title: 'My Tasks',
    taskTitle: 'Task Title',
    taskTitlePlaceholder: 'Enter task title...',
    priority: 'Priority',
    dueDate: 'Due Date',
    addTask: 'Add Task',
    noTasks: 'No tasks yet. Add your first task above!',
    deleteTask: 'Delete task',
    confirmDelete: 'Delete "{title}"? This cannot be undone.'
  },

  // Language
  language: {
    english: 'English',
    japanese: 'Japanese',
    selectLanguage: 'Select Language'
  },

  // Common
  common: {
    loading: 'Loading...',
    error: 'Error',
    noData: 'No data available',
    viewDetails: 'View Details',
    close: 'Close',
    save: 'Save',
    cancel: 'Cancel',
    search: 'Search',
    filter: 'Filter',
    export: 'Export',
    exportCsv: 'Export CSV',
    exportCsvTitle: 'Download the rows currently shown as a CSV file',
    items: 'items'
  }
}
