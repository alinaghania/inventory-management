<template>
  <div class="demand">
    <div class="page-header">
      <h2>{{ t('demand.title') }}</h2>
      <p>{{ t('demand.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="demand-trend-cards">
        <div class="trend-card increasing-card">
          <div class="trend-header">
            <div class="trend-icon">↑</div>
            <div>
              <div class="trend-label">{{ t('demand.increasingDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: forecastsByTrend.increasing.length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in forecastsByTrend.increasing.slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">+{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="forecastsByTrend.increasing.length > 5" class="more-items">
              +{{ forecastsByTrend.increasing.length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="trend-card stable-card">
          <div class="trend-header">
            <div class="trend-icon">→</div>
            <div>
              <div class="trend-label">{{ t('demand.stableDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: forecastsByTrend.stable.length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in forecastsByTrend.stable.slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change neutral">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="forecastsByTrend.stable.length > 5" class="more-items">
              +{{ forecastsByTrend.stable.length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="trend-card decreasing-card">
          <div class="trend-header">
            <div class="trend-icon">↓</div>
            <div>
              <div class="trend-label">{{ t('demand.decreasingDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: forecastsByTrend.decreasing.length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in forecastsByTrend.decreasing.slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="forecastsByTrend.decreasing.length > 5" class="more-items">
              +{{ forecastsByTrend.decreasing.length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('demand.demandForecasts') }}</h3>
          <button
            class="btn btn-secondary"
            :disabled="forecasts.length === 0"
            :title="t('common.exportCsvTitle')"
            @click="exportForecastsCsv"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.75 2.75a.75.75 0 00-1.5 0v8.614L6.295 8.235a.75.75 0 10-1.09 1.03l4.25 4.5a.75.75 0 001.09 0l4.25-4.5a.75.75 0 00-1.09-1.03l-2.955 3.129V2.75z" />
              <path d="M3.5 12.75a.75.75 0 00-1.5 0v2.5A2.75 2.75 0 004.75 18h10.5A2.75 2.75 0 0018 15.25v-2.5a.75.75 0 00-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5z" />
            </svg>
            {{ t('common.exportCsv') }}
          </button>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('demand.table.sku') }}</th>
                <th>{{ t('demand.table.itemName') }}</th>
                <th>{{ t('demand.table.currentDemand') }}</th>
                <th>{{ t('demand.table.forecastedDemand') }}</th>
                <th>{{ t('demand.table.change') }}</th>
                <th>{{ t('demand.table.trend') }}</th>
                <th>{{ t('demand.table.period') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="forecast in forecasts" :key="forecast.id">
                <td><strong>{{ forecast.item_sku }}</strong></td>
                <td>{{ forecast.item_name }}</td>
                <td>{{ forecast.current_demand }}</td>
                <td><strong>{{ forecast.forecasted_demand }}</strong></td>
                <td>
                  <span :style="{ color: getChangeColor(forecast) }">
                    {{ getChangePercent(forecast) }}%
                  </span>
                </td>
                <td>
                  <span :class="['badge', forecast.trend]">
                    {{ t(`trends.${forecast.trend}`) }}
                  </span>
                </td>
                <td>{{ translatePeriod(forecast.period) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { useCsvExport } from '../composables/useCsvExport'

export default {
  name: 'Demand',
  setup() {
    const { t, currentLocale } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const inventoryItems = ref([])

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const { exportCsv } = useCsvExport()

    // Filter forecasts based on inventory filters
    const forecasts = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allForecasts.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allForecasts.value.filter(f => validSkus.has(f.item_sku))
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        allForecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadForecasts()
    })

    // Grouped once per forecasts change rather than re-filtered by each of the
    // twelve template call sites on every render
    const forecastsByTrend = computed(() => {
      const groups = { increasing: [], stable: [], decreasing: [] }
      forecasts.value.forEach(forecast => {
        if (groups[forecast.trend]) groups[forecast.trend].push(forecast)
      })
      return groups
    })

    const getChangePercent = (forecast) => {
      const change = ((forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand * 100).toFixed(1)
      return change > 0 ? `+${change}` : change
    }

    const getChangeColor = (forecast) => {
      const change = forecast.forecasted_demand - forecast.current_demand
      const changePercent = Math.abs((change / forecast.current_demand) * 100)

      // If change is within ±2%, consider it stable and show blue
      if (changePercent <= 2) {
        return '#3b82f6' // Blue for stable
      }

      if (change > 0) return '#10b981' // Green for increasing
      if (change < 0) return '#ef4444' // Red for decreasing
      return '#3b82f6' // Blue for no change
    }

    const translatePeriod = (period) => {
      // Period values like "Next 3 months", "Q1 2025", "30 days", etc.
      if (currentLocale.value === 'ja') {
        return period
          .replace(/Next\s+/i, '次の')
          .replace(/\s+months/i, 'か月')
          .replace(/\s+month/i, 'か月')
          .replace(/\s+days/i, '日間')
          .replace(/\s+day/i, '日')
          .replace('Q1', '第1四半期')
          .replace('Q2', '第2四半期')
          .replace('Q3', '第3四半期')
          .replace('Q4', '第4四半期')
      }
      return period
    }

    // The change column exports as a bare signed number, without the "%" the
    // table appends, so the spreadsheet can chart it.
    const exportForecastsCsv = () => {
      const columns = [
        { header: t('demand.table.sku'), value: (forecast) => forecast.item_sku },
        { header: t('demand.table.itemName'), value: (forecast) => forecast.item_name },
        { header: t('demand.table.currentDemand'), value: (forecast) => forecast.current_demand },
        { header: t('demand.table.forecastedDemand'), value: (forecast) => forecast.forecasted_demand },
        { header: `${t('demand.table.change')} (%)`, value: (forecast) => getChangePercent(forecast) },
        { header: t('demand.table.trend'), value: (forecast) => t(`trends.${forecast.trend}`) },
        { header: t('demand.table.period'), value: (forecast) => translatePeriod(forecast.period) }
      ]

      exportCsv('demand-forecasts', columns, forecasts.value)
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      forecasts,
      forecastsByTrend,
      getChangePercent,
      getChangeColor,
      translatePeriod,
      exportForecastsCsv
    }
  }
}
</script>

<style scoped>
.demand-trend-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.trend-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.5rem;
  transition: all 0.2s ease;
}

.trend-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.increasing-card {
  border-left: 4px solid #10b981;
}

.stable-card {
  border-left: 4px solid var(--brand-700);
}

.decreasing-card {
  border-left: 4px solid #ef4444;
}

.trend-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--surface-muted);
}

.trend-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 1.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.increasing-card .trend-icon {
  background: #d1fae5;
  color: #059669;
}

.stable-card .trend-icon {
  background: #dbeafe;
  color: var(--brand-900);
}

.decreasing-card .trend-icon {
  background: #fee2e2;
  color: #dc2626;
}

.trend-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.trend-count {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
  margin-top: 0.25rem;
}

.trend-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.trend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: var(--surface-muted);
  border-radius: 6px;
  transition: background 0.2s;
}

.trend-item:hover {
  background: var(--surface-muted);
}

.item-name {
  font-size: 0.875rem;
  color: var(--text);
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 1rem;
}

.item-change {
  font-size: 0.813rem;
  font-weight: 700;
  flex-shrink: 0;
}

.increasing-card .item-change {
  color: #059669;
}

.stable-card .item-change {
  color: var(--brand-700);
}

.decreasing-card .item-change {
  color: #dc2626;
}

.item-change.neutral {
  color: var(--text-muted);
}

.more-items {
  font-size: 0.813rem;
  color: var(--text-muted);
  font-style: italic;
  text-align: center;
  padding: 0.5rem;
}
</style>
