<template>
  <div class="reports">
    <div class="page-header">
      <h2>Performance Reports</h2>
      <p>View quarterly performance metrics and monthly trends</p>
    </div>

    <div v-if="loading" class="loading">Loading reports...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="!hasData" class="empty-state">
      No orders match the current filters. Adjust or reset the filters to see reports.
    </div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Quarterly Performance</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>Quarter</th>
                <th>Total Orders</th>
                <th>Total Revenue</th>
                <th>Avg Order Value</th>
                <th>Fulfillment Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td>{{ q.total_orders }}</td>
                <td>${{ formatNumber(q.total_revenue) }}</td>
                <td>${{ formatNumber(q.avg_order_value) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Monthly Revenue Trend</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="'$' + formatNumber(month.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(month.month) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Month-over-Month Analysis</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>Orders</th>
                <th>Revenue</th>
                <th>Change</th>
                <th>Growth Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, index) in monthlyData" :key="month.month">
                <td><strong>{{ formatMonth(month.month) }}</strong></td>
                <td>{{ month.order_count }}</td>
                <td>${{ formatNumber(month.revenue) }}</td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getChangeValue(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getGrowthRate(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total Revenue ({{ totalsScope }})</div>
          <div class="stat-value">${{ formatNumber(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Avg Monthly Revenue</div>
          <div class="stat-value">${{ formatNumber(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Orders ({{ totalsScope }})</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Best Performing Quarter</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// Tallest bar in the revenue chart, in pixels
const CHART_MAX_HEIGHT = 200

export default {
  name: 'Reports',
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      getCurrentFilters
    } = useFilters()

    const loadData = async () => {
      try {
        loading.value = true
        // Cleared on every attempt, otherwise one failed load would keep the
        // error banner up for all subsequent filter changes
        error.value = null

        const filters = getCurrentFilters()

        // The two reports are independent, so request them together rather
        // than paying both round-trips back to back
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])
        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        error.value = 'Failed to load reports. Please try again.'
        console.error('Reports load failed:', err)
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    // A filter combination can legitimately match no orders at all
    const hasData = computed(() => quarterlyData.value.length > 0 || monthlyData.value.length > 0)

    // Every bar needs the series maximum to size itself. As a method this was
    // recomputed per bar, making the chart O(n^2); as a computed it is cached
    // until monthlyData changes.
    const maxMonthlyRevenue = computed(() =>
      monthlyData.value.reduce((max, month) => Math.max(max, month.revenue), 0)
    )

    // Single pass shared by both totals rather than one reduce per stat card
    const totals = computed(() =>
      monthlyData.value.reduce(
        (acc, month) => {
          acc.revenue += month.revenue
          acc.orders += month.order_count
          return acc
        },
        { revenue: 0, orders: 0 }
      )
    )

    const totalRevenue = computed(() => totals.value.revenue)
    const totalOrders = computed(() => totals.value.orders)

    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length ? totals.value.revenue / monthlyData.value.length : 0
    )

    const bestQuarter = computed(() => {
      const best = quarterlyData.value.reduce(
        (leader, quarter) => (quarter.total_revenue > leader.total_revenue ? quarter : leader),
        { quarter: '', total_revenue: 0 }
      )
      return best.quarter || '-'
    })

    // These totals only span the year when nothing is filtered - under a month
    // or warehouse filter they cover the selected slice, so don't claim "YTD"
    const totalsScope = computed(() => (hasActiveFilters.value ? 'Filtered' : 'YTD'))

    const formatNumber = (num) =>
      Number(num).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })

    const formatMonth = (monthStr) => {
      // Convert YYYY-MM to readable format
      const [year, month] = monthStr.split('-')
      return `${MONTH_NAMES[parseInt(month, 10) - 1]} ${year}`
    }

    const getBarHeight = (revenue) => {
      if (maxMonthlyRevenue.value === 0) return 0
      return (revenue / maxMonthlyRevenue.value) * CHART_MAX_HEIGHT
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) {
        return 'badge success'
      } else if (rate >= 75) {
        return 'badge warning'
      } else {
        return 'badge danger'
      }
    }

    const getChangeValue = (current, previous) => {
      const change = current - previous
      if (change > 0) {
        return '+$' + formatNumber(change)
      } else if (change < 0) {
        return '-$' + formatNumber(Math.abs(change))
      } else {
        return '$0.00'
      }
    }

    const getChangeClass = (current, previous) => {
      const change = current - previous
      if (change > 0) {
        return 'positive-change'
      } else if (change < 0) {
        return 'negative-change'
      } else {
        return ''
      }
    }

    const getGrowthRate = (current, previous) => {
      if (previous === 0) {
        return 'N/A'
      }

      const rate = ((current - previous) / previous) * 100
      const sign = rate > 0 ? '+' : ''

      return sign + rate.toFixed(1) + '%'
    }

    onMounted(loadData)

    return {
      loading,
      error,
      quarterlyData,
      monthlyData,
      hasData,
      totalRevenue,
      totalOrders,
      avgMonthlyRevenue,
      bestQuarter,
      totalsScope,
      formatNumber,
      formatMonth,
      getBarHeight,
      getFulfillmentClass,
      getChangeValue,
      getChangeClass,
      getGrowthRate
    }
  }
}
</script>

<style scoped>
.reports {
  padding: 0;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: var(--surface-muted);
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 2px solid var(--border);
}

.reports-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.reports-table tr:hover {
  background: var(--surface-muted);
}

.chart-container {
  padding: 2rem 1rem;
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: 0.5rem;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: linear-gradient(to top, var(--brand-700), var(--brand-500));
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, var(--brand-900), var(--brand-700));
}

.bar-label {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid var(--brand-700);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--text);
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.badge.success {
  background: #dcfce7;
  color: #166534;
}

.badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.badge.danger {
  background: #fee2e2;
  color: #991b1b;
}

.positive-change {
  color: #16a34a;
  font-weight: 600;
}

.negative-change {
  color: #dc2626;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.error {
  background: #fee2e2;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
}

.empty-state {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}
</style>
