<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.budgetQuestion', { budget: formatCurrency(budget, currency) }) }}
          </h3>
        </div>

        <div class="budget-body">
          <div class="budget-readout">{{ formatCurrency(budget, currency) }}</div>
          <p class="budget-help">{{ t('restocking.budgetHelp') }}</p>

          <div class="slider-row">
            <span class="slider-bound">{{ formatCurrency(0, currency) }}</span>
            <input
              v-model.number="budget"
              type="range"
              class="budget-slider"
              min="0"
              :max="sliderMax"
              :step="sliderStep"
            />
            <span class="slider-bound">{{ formatCurrency(sliderMax, currency) }}</span>
          </div>

          <div class="budget-meter">
            <div
              class="budget-meter-fill"
              :class="{ over: isOverBudget }"
              :style="{ width: budgetUsedPercent + '%' }"
            ></div>
          </div>

          <div class="budget-figures">
            <div class="budget-figure">
              <div class="figure-label">{{ t('restocking.budgetTitle') }}</div>
              <div class="figure-value">{{ formatCurrency(budget, currency) }}</div>
            </div>
            <div class="budget-figure">
              <div class="figure-label">{{ t('restocking.budgetUsed') }}</div>
              <div class="figure-value">{{ formatCurrency(allocatedCost, currency) }}</div>
            </div>
            <div class="budget-figure">
              <div class="figure-label">
                {{ isOverBudget ? t('restocking.overBudget') : t('restocking.budgetRemaining') }}
              </div>
              <div class="figure-value" :class="{ negative: isOverBudget }">
                {{ formatCurrency(Math.abs(remainingBudget), currency) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <div class="header-actions">
            <span class="funded-summary">
              {{ t('restocking.itemsRecommended', {
                count: selectedRows.length,
                total: recommendations.length
              }) }}
            </span>
            <button class="link-btn" :disabled="!recommendations.length" @click="selectAll">
              {{ t('restocking.selectAll') }}
            </button>
            <button class="link-btn" :disabled="!recommendations.length" @click="clearAll">
              {{ t('restocking.clearAll') }}
            </button>
          </div>
        </div>

        <div v-if="!recommendations.length" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>

        <template v-else>
          <div v-if="showIncreaseBudgetHint" class="budget-hint">
            {{ t('restocking.increaseBudget', {
              amount: formatCurrency(summary.cheapest_unit_cost, currency)
            }) }}
          </div>

          <div class="table-container">
            <table class="restocking-table">
              <thead>
                <tr>
                  <th class="col-include">{{ t('restocking.table.include') }}</th>
                  <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                  <th class="col-name">{{ t('restocking.table.itemName') }}</th>
                  <th class="col-category">{{ t('restocking.table.category') }}</th>
                  <th class="col-warehouse">{{ t('restocking.table.warehouse') }}</th>
                  <th class="col-num">{{ t('restocking.table.onHand') }}</th>
                  <th class="col-num">{{ t('restocking.table.forecast') }}</th>
                  <th class="col-num">{{ t('restocking.table.shortfall') }}</th>
                  <th class="col-trend">{{ t('restocking.table.trend') }}</th>
                  <th class="col-num">{{ t('restocking.table.unitCost') }}</th>
                  <th class="col-lead">{{ t('restocking.table.leadTime') }}</th>
                  <th class="col-qty">{{ t('restocking.table.quantity') }}</th>
                  <th class="col-num">{{ t('restocking.table.lineCost') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in recommendations"
                  :key="row.sku"
                  :class="{
                    'row-excluded': excluded[row.sku],
                    'row-urgent': row.below_reorder_point
                  }"
                >
                  <td class="col-include">
                    <input
                      type="checkbox"
                      :checked="!excluded[row.sku]"
                      @change="toggleRow(row.sku)"
                    />
                  </td>
                  <td class="col-sku"><strong>{{ row.sku }}</strong></td>
                  <td class="col-name">
                    <span
                      v-if="row.below_reorder_point"
                      class="urgent-marker"
                      :title="t('restocking.belowReorder')"
                    >!</span>
                    {{ translateProductName(row.item_name) }}
                  </td>
                  <td class="col-category">{{ row.category }}</td>
                  <td class="col-warehouse">{{ translateWarehouse(row.warehouse) }}</td>
                  <td class="col-num">{{ row.quantity_on_hand.toLocaleString() }}</td>
                  <td class="col-num">{{ row.forecasted_demand.toLocaleString() }}</td>
                  <td class="col-num"><strong>{{ row.projected_shortfall.toLocaleString() }}</strong></td>
                  <td class="col-trend">
                    <span :class="['badge', row.trend]">{{ t(`trends.${row.trend}`) }}</span>
                  </td>
                  <td class="col-num">{{ formatCurrency(row.unit_cost, currency) }}</td>
                  <td class="col-lead">{{ t('restocking.daysUnit', { count: row.lead_time_days }) }}</td>
                  <td class="col-qty">
                    <input
                      class="qty-input"
                      type="number"
                      min="0"
                      :max="row.projected_shortfall"
                      :value="quantities[row.sku]"
                      :disabled="excluded[row.sku]"
                      @input="updateQuantity(row, $event.target.value)"
                    />
                  </td>
                  <td class="col-num">
                    <strong>{{ formatCurrency(lineCost(row), currency) }}</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="action-bar">
            <div class="action-totals">
              <div class="action-total">
                <span class="figure-label">{{ t('restocking.totalUnits') }}</span>
                <span class="figure-value">{{ totalUnits.toLocaleString() }}</span>
              </div>
              <div class="action-total">
                <span class="figure-label">{{ t('restocking.totalCost') }}</span>
                <span class="figure-value" :class="{ negative: isOverBudget }">
                  {{ formatCurrency(allocatedCost, currency) }}
                </span>
              </div>
            </div>

            <div class="action-controls">
              <div
                v-if="submitResult"
                :class="['submit-banner', submitResult.type]"
              >{{ submitResult.message }}</div>
              <button class="place-order-btn" :disabled="!canPlaceOrder" @click="placeOrder">
                {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

// A range input fires continuously while dragging, so budget changes are
// debounced before hitting the API
const BUDGET_DEBOUNCE_MS = 300

// Slider bounds are rounded to this increment so the max reads as a round number
const SLIDER_MAX_INCREMENT = 5000

// Fraction of the maximum useful budget to start on. Lands mid-allocation so
// the page opens on a meaningful partial plan rather than an empty or full one.
const INITIAL_BUDGET_RATIO = 0.3

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const loading = ref(true)
    const error = ref(null)

    // Raw server state - never mutated locally
    const recommendations = ref([])
    const summary = ref(null)

    // User controls
    const budget = ref(0)
    const sliderMax = ref(0)
    const quantities = ref({})
    const excluded = ref({})

    const submitting = ref(false)
    const submitResult = ref(null)

    // Set while the initial budget is being derived so seeding it doesn't
    // trigger a duplicate fetch through the watcher
    let suppressBudgetWatch = false
    let budgetTimer = null

    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const currency = computed(() => currentCurrency.value)

    const sliderStep = computed(() => {
      return Math.max(100, Math.round(sliderMax.value / 100 / 100) * 100)
    })

    const lineCost = (row) => (quantities.value[row.sku] || 0) * row.unit_cost

    const selectedRows = computed(() => {
      return recommendations.value.filter(
        row => !excluded.value[row.sku] && (quantities.value[row.sku] || 0) > 0
      )
    })

    const allocatedCost = computed(() => {
      return selectedRows.value.reduce((sum, row) => sum + lineCost(row), 0)
    })

    const totalUnits = computed(() => {
      return selectedRows.value.reduce((sum, row) => sum + quantities.value[row.sku], 0)
    })

    const remainingBudget = computed(() => budget.value - allocatedCost.value)
    const isOverBudget = computed(() => remainingBudget.value < 0)

    // Guard against a zero budget so the meter never divides by zero
    const budgetUsedPercent = computed(() => {
      if (budget.value <= 0) return 0
      return Math.min(100, (allocatedCost.value / budget.value) * 100)
    })

    const canPlaceOrder = computed(() => {
      return selectedRows.value.length > 0 && !isOverBudget.value && !submitting.value
    })

    // Candidates exist but the budget can't cover even the cheapest single unit
    const showIncreaseBudgetHint = computed(() => {
      return Boolean(
        summary.value &&
        summary.value.cheapest_unit_cost !== null &&
        recommendations.value.length > 0 &&
        summary.value.items_recommended === 0
      )
    })

    const loadRecommendations = async () => {
      try {
        error.value = null
        const filters = getCurrentFilters()
        const data = await api.getRestockingRecommendations(budget.value, {
          warehouse: filters.warehouse,
          category: filters.category
        })

        recommendations.value = data.recommendations
        summary.value = data

        // Reseed from the server allocation on every fetch. This deliberately
        // discards manual quantity edits: keeping them across a re-allocation
        // would make the budget meter disagree with what the server allocated.
        quantities.value = Object.fromEntries(
          data.recommendations.map(row => [row.sku, row.suggested_quantity])
        )
        excluded.value = {}
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const updateQuantity = (row, rawValue) => {
      // A cleared number input yields '' and Number('') is 0, but a partial
      // entry like '-' yields NaN, which would poison every downstream total
      const parsed = Number(rawValue)
      const safe = Number.isFinite(parsed) ? Math.floor(parsed) : 0
      quantities.value[row.sku] = Math.min(Math.max(safe, 0), row.projected_shortfall)
    }

    const toggleRow = (sku) => {
      if (excluded.value[sku]) {
        delete excluded.value[sku]
      } else {
        excluded.value[sku] = true
      }
    }

    const selectAll = () => {
      excluded.value = {}
    }

    const clearAll = () => {
      excluded.value = Object.fromEntries(
        recommendations.value.map(row => [row.sku, true])
      )
    }

    const placeOrder = async () => {
      submitting.value = true
      submitResult.value = null

      try {
        // Send SKU and quantity only - the server prices the order itself
        const order = await api.createRestockingOrder({
          budget: budget.value,
          items: selectedRows.value.map(row => ({
            sku: row.sku,
            quantity: quantities.value[row.sku]
          }))
        })

        submitResult.value = {
          type: 'success',
          message: t('restocking.orderPlaced', { orderNumber: order.order_number })
        }

        // Reset the form to a fresh allocation for the same budget
        await loadRecommendations()
      } catch (err) {
        submitResult.value = {
          type: 'error',
          message: t('restocking.orderFailed', {
            message: err.response?.data?.detail || err.message
          })
        }
      } finally {
        submitting.value = false
      }
    }

    watch(budget, () => {
      if (suppressBudgetWatch) return
      clearTimeout(budgetTimer)
      budgetTimer = setTimeout(loadRecommendations, BUDGET_DEBOUNCE_MS)
    })

    // Restocking has no time or order-status dimension, so only the warehouse
    // and category filters apply. Filter changes fetch immediately.
    watch([selectedLocation, selectedCategory], loadRecommendations)

    onMounted(async () => {
      // First pass runs at budget 0 purely to learn max_useful_budget, which
      // sets the slider bounds
      await loadRecommendations()

      const maxUseful = summary.value?.max_useful_budget || 0
      sliderMax.value = Math.max(
        SLIDER_MAX_INCREMENT,
        Math.ceil(maxUseful / SLIDER_MAX_INCREMENT) * SLIDER_MAX_INCREMENT
      )

      suppressBudgetWatch = true
      budget.value = Math.round(
        (sliderMax.value * INITIAL_BUDGET_RATIO) / sliderStep.value
      ) * sliderStep.value
      suppressBudgetWatch = false

      await loadRecommendations()
    })

    onUnmounted(() => {
      clearTimeout(budgetTimer)
    })

    return {
      t,
      loading,
      error,
      recommendations,
      summary,
      budget,
      sliderMax,
      sliderStep,
      quantities,
      excluded,
      submitting,
      submitResult,
      currency,
      selectedRows,
      allocatedCost,
      totalUnits,
      remainingBudget,
      isOverBudget,
      budgetUsedPercent,
      canPlaceOrder,
      showIncreaseBudgetHint,
      lineCost,
      updateQuantity,
      toggleRow,
      selectAll,
      clearAll,
      placeOrder,
      formatCurrency,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
/* Budget card */
.budget-body {
  padding: 1.5rem;
}

.budget-readout {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1.1;
}

.budget-help {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0.375rem 0 1.5rem;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.slider-bound {
  font-size: 0.813rem;
  font-weight: 600;
  color: var(--text-muted);
  flex-shrink: 0;
  min-width: 70px;
}

.slider-bound:last-child {
  text-align: right;
}

/* Native range input, restyled to match the design system */
.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: var(--border);
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--brand-900);
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: transform 0.15s;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--brand-900);
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-slider:focus {
  outline: none;
}

.budget-slider:focus::-webkit-slider-thumb {
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
}

/* Allocation meter */
.budget-meter {
  height: 10px;
  border-radius: 5px;
  background: var(--border);
  overflow: hidden;
  margin-top: 1.5rem;
}

.budget-meter-fill {
  height: 100%;
  background: var(--brand-900);
  border-radius: 5px;
  transition: width 0.2s ease, background 0.2s ease;
}

.budget-meter-fill.over {
  background: #dc2626;
}

.budget-figures {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-top: 1.25rem;
}

.figure-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.figure-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text);
  margin-top: 0.25rem;
}

.figure-value.negative {
  color: #dc2626;
}

/* Recommendations card */
.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.funded-summary {
  font-size: 0.813rem;
  color: var(--text-muted);
  font-weight: 500;
}

.link-btn {
  background: none;
  border: none;
  color: var(--brand-900);
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.link-btn:hover:not(:disabled) {
  text-decoration: underline;
}

.link-btn:disabled {
  color: var(--text-faint);
  cursor: not-allowed;
}

.empty-state {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.938rem;
}

.budget-hint {
  margin: 1rem 1.5rem 0;
  padding: 0.75rem 1rem;
  background: var(--brand-50);
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #1e40af;
}

.restocking-table {
  width: 100%;
}

.col-include {
  width: 70px;
  text-align: center;
}

.col-sku {
  width: 100px;
}

.col-category,
.col-warehouse {
  width: 130px;
}

.col-num {
  width: 100px;
  text-align: right;
}

.col-trend {
  width: 110px;
}

.col-lead {
  width: 100px;
}

.col-qty {
  width: 110px;
}

.row-urgent td {
  background: #fffbeb;
}

.row-excluded {
  opacity: 0.4;
}

.urgent-marker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fef3c7;
  color: #b45309;
  font-size: 0.688rem;
  font-weight: 700;
  margin-right: 0.375rem;
  cursor: help;
}

.qty-input {
  width: 90px;
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text);
  text-align: right;
}

.qty-input:focus {
  outline: none;
  border-color: var(--brand-700);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.qty-input:disabled {
  background: var(--surface-muted);
  color: var(--text-faint);
}

/* Action bar */
.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--border);
  background: var(--surface-muted);
  flex-wrap: wrap;
}

.action-totals {
  display: flex;
  gap: 2.5rem;
}

.action-total {
  display: flex;
  flex-direction: column;
}

.action-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.submit-banner {
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.5rem 0.875rem;
  border-radius: 6px;
}

.submit-banner.success {
  background: #d1fae5;
  color: #065f46;
}

.submit-banner.error {
  background: #fee2e2;
  color: #991b1b;
}

.place-order-btn {
  padding: 0.625rem 1.75rem;
  background: var(--brand-900);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: var(--brand-900);
}

.place-order-btn:disabled {
  background: var(--border-strong);
  cursor: not-allowed;
}
</style>
