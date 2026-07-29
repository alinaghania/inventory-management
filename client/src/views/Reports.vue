<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('reports.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="!hasData" class="empty-state">{{ t('reports.emptyState') }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.quarterly.quarter') }}</th>
                <th>{{ t('reports.quarterly.totalOrders') }}</th>
                <th>{{ t('reports.quarterly.totalRevenue') }}</th>
                <th>{{ t('reports.quarterly.avgOrderValue') }}</th>
                <th>{{ t('reports.quarterly.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ formatQuarter(q.quarter) }}</strong></td>
                <td>{{ q.total_orders }}</td>
                <td>{{ formatMoney(q.total_revenue) }}</td>
                <td>{{ formatMoney(q.avg_order_value) }}</td>
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
          <h3 class="card-title">{{ t('reports.monthlyTrend.title') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="formatMoney(month.revenue)"
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
          <h3 class="card-title">{{ t('reports.monthOverMonth.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.monthOverMonth.month') }}</th>
                <th>{{ t('reports.monthOverMonth.orders') }}</th>
                <th>{{ t('reports.monthOverMonth.revenue') }}</th>
                <th>{{ t('reports.monthOverMonth.change') }}</th>
                <th>{{ t('reports.monthOverMonth.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, index) in monthlyData" :key="month.month">
                <td><strong>{{ formatMonth(month.month) }}</strong></td>
                <td>{{ month.order_count }}</td>
                <td>{{ formatMoney(month.revenue) }}</td>
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
          <div class="stat-label">{{ totalRevenueLabel }}</div>
          <div class="stat-value">{{ formatMoney(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ totalOrdersLabel }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.bestQuarter') }}</div>
          <div class="stat-value">{{ formatQuarter(bestQuarter) || '-' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { useFilters } from '../composables/useFilters'
import { formatCurrencyWithDecimals } from '../utils/currency'

// Index maps the numeric month from the API's "YYYY-MM" strings onto the
// shared `months.*` locale keys, so month labels follow the active language.
const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

// Tallest bar in the revenue chart, in pixels
const CHART_MAX_HEIGHT = 200

export default {
  name: 'Reports',
  setup() {
    const { t, currentCurrency } = useI18n()

    const loading = ref(true)
    const errorMessage = ref(null)
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

    // Kept as a computed (not a plain ref) so the message re-translates when the
    // user switches language after a failed load.
    const error = computed(() => {
      if (!errorMessage.value) return null
      return t('reports.loadError', { message: errorMessage.value })
    })

    const loadData = async () => {
      try {
        loading.value = true
        // Cleared on every attempt, otherwise one failed load would keep the
        // error banner up for all subsequent filter changes
        errorMessage.value = null

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
        console.error('Reports load failed:', err)
        errorMessage.value = err.message
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
      return best.quarter
    })

    // These totals only span the year when nothing is filtered - under a month
    // or warehouse filter they cover the selected slice, so don't claim "YTD"
    const totalRevenueLabel = computed(() =>
      t(hasActiveFilters.value
        ? 'reports.stats.totalRevenueFiltered'
        : 'reports.stats.totalRevenueYtd')
    )

    const totalOrdersLabel = computed(() =>
      t(hasActiveFilters.value
        ? 'reports.stats.totalOrdersFiltered'
        : 'reports.stats.totalOrdersYtd')
    )

    // Converts and formats through the shared currency helper so JA renders yen
    // instead of the dollar sign that used to be hardcoded in the template.
    const formatMoney = (amount) => {
      return formatCurrencyWithDecimals(amount, currentCurrency.value, 2)
    }

    // The API returns quarter codes as "Q1-2025"; the locale template decides
    // the part order (EN "Q1 2025" vs JA "2025年 第1四半期").
    const formatQuarter = (quarterCode) => {
      if (!quarterCode) return ''
      const parts = /^Q(\d)-(\d{4})$/.exec(quarterCode)
      if (!parts) return quarterCode
      return t('reports.quarterFormat', { quarter: parts[1], year: parts[2] })
    }

    // Converts "YYYY-MM" into a localized label (EN "Jan 2025", JA "2025年1月").
    const formatMonth = (monthStr) => {
      if (!monthStr) return ''
      const [year, month] = monthStr.split('-')
      const monthKey = MONTH_KEYS[parseInt(month, 10) - 1]
      if (!monthKey) return monthStr
      return t('reports.monthFormat', { month: t(`months.${monthKey}`), year })
    }

    const getBarHeight = (revenue) => {
      if (maxMonthlyRevenue.value === 0) return 0
      return (revenue / maxMonthlyRevenue.value) * CHART_MAX_HEIGHT
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    const getChangeValue = (current, previous) => {
      const change = current - previous
      if (change > 0) return `+${formatMoney(change)}`
      if (change < 0) return `-${formatMoney(Math.abs(change))}`
      return formatMoney(0)
    }

    const getChangeClass = (current, previous) => {
      const change = current - previous
      if (change > 0) return 'positive-change'
      if (change < 0) return 'negative-change'
      return ''
    }

    const getGrowthRate = (current, previous) => {
      if (previous === 0) return t('reports.notAvailable')
      const rate = ((current - previous) / previous) * 100
      const sign = rate > 0 ? '+' : ''
      return `${sign}${rate.toFixed(1)}%`
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      quarterlyData,
      monthlyData,
      hasData,
      totalRevenue,
      totalOrders,
      avgMonthlyRevenue,
      bestQuarter,
      totalRevenueLabel,
      totalOrdersLabel,
      formatMoney,
      formatQuarter,
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
  border-radius: 4px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: none;
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
  background: var(--chart-1);
  border-radius: 2px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: var(--chart-2);
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
  border-radius: 4px;
  padding: 1.5rem;
  box-shadow: none;
  border: 1px solid var(--border);
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
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

.badge.success {
  background: #edf3ee;
  color: #2f5d43;
}

.badge.warning {
  background: #f7f1e3;
  color: #9c7c2e;
}

.badge.danger {
  background: #f8eded;
  color: #8c3a3a;
}

.positive-change {
  color: #2f5d43;
  font-weight: 600;
}

.negative-change {
  color: #8c3a3a;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.error {
  background: #f8eded;
  color: #8c3a3a;
  padding: 1rem;
  border-radius: 4px;
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
