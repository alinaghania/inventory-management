# Detection patterns and fix recipes

Run from `client/src`. Each pattern: how to find it, how to confirm it, how to fix it, and
when **not** to report it.

---

## 1. Uncached template methods

Vue caches `computed()` until dependencies change. A method re-runs on **every render**.
Cheap for a lookup, expensive for an array scan.

### Detect

```bash
# Method calls in templates, excluding known-cheap ones
grep -rn "{{ [a-z][A-Za-z]*(" views components | grep -v "formatCurrency\|^.*t(" 
```

### Confirm

Open each hit and check the definition. Report only if **both**:
- it's `const fn = (...) => {...}`, not `computed(...)`, **and**
- the body scans an array (`.filter`, `.map`, `.reduce`, `.sort`, `.find` over a `ref`)

### Fix — no argument

```js
// Before: re-scans on every render
const lowStockItems = () => items.value.filter(i => i.quantity_on_hand < i.reorder_point)

// After: cached until items changes
const lowStockItems = computed(() =>
  items.value.filter(i => i.quantity_on_hand < i.reorder_point)
)
```

### Fix — called with a fixed set of arguments

When the template calls `getOrdersByStatus('Delivered')`, `'Shipped'`, `'Processing'`,
`'Backordered'` — four scans per render. Group once instead:

```js
// One pass, cached. Template reads ordersByStatus.Delivered.length
const ordersByStatus = computed(() => {
  const grouped = { Delivered: [], Shipped: [], Processing: [], Backordered: [] }
  for (const order of orders.value) {
    // Unknown statuses are ignored rather than creating stray buckets
    if (grouped[order.status]) grouped[order.status].push(order)
  }
  return grouped
})
```

Keep the method too if other code calls it with a dynamic value — the computed is for the
template's fixed calls.

### Don't report

- Called once, with an argument → a computed would need a factory. Not worth it.
- Body is an object/dictionary lookup (`translateProductName`, `translateWarehouse`) → O(1).
- Body is pure string formatting on a scalar → cheap.

---

## 2. Composables invoked inside function bodies

`useI18n()` inside a formatter runs the whole composable **per call** — and inside a `v-for`
that's per row, per render.

### Detect

```bash
grep -rn -B4 "= useI18n()" views components | grep -A4 "const .* = ("
```

### Confirm

The `useI18n()` call sits inside a function body rather than at the top of `setup()`.

### Fix

Hoist to `setup()` scope:

```js
// Before
const formatDate = (dateString) => {
  const { currentLocale } = useI18n()        // per call
  ...
}

// After
const { currentLocale } = useI18n()          // once, in setup()
const formatDate = (dateString) => { ... }
```

Safe: `useI18n` returns refs from module-level state, so hoisting changes nothing about
reactivity. Verify by toggling to Japanese after the change.

---

## 3. Drifted duplicate helpers

The high-value category. Same-named helpers copied across files, then edited in one place
only — so the duplication is now hiding **behavioral differences**.

### Detect

```bash
grep -rn "const format[A-Za-z]* = \|const get[A-Za-z]*Class = \|const translate[A-Za-z]* = " \
  views components | sed 's/:.*const /  /' | sort | uniq -c | sort -rn
```

### Confirm — this is the step that matters

Print every implementation side by side and **diff the behavior**, not the text:

```bash
for f in <files>; do echo "--- $f"; grep -A8 "const formatDate = " "$f"; done
```

Compare along three axes:

| Axis | Question |
| --- | --- |
| **Null/empty input** | `''`, `'-'`, `'N/A'`, or an unguarded `Invalid Date`? |
| **Locale** | Hardcoded `'en-US'`, or reads `currentLocale`? |
| **Output shape** | `month: 'short'` vs `'long'`; year included or not? |

Any divergence on the locale axis is a **live i18n bug** — report it as a correctness finding
first and a DRY finding second.

### Fix

Consolidate into `utils/` (alongside the existing `utils/currency.js`, which is the
established pattern for this).

The consolidated version must be a **superset** — it has to satisfy every call site:

```js
// utils/date.js
// Callers disagreed on the empty-value placeholder, so it's a parameter rather than
// picking one and silently changing five screens.
export function formatDate(dateString, { locale, style = 'short', empty = '-' } = {}) {
  if (!dateString) return empty
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return empty        // guard the whole family at once
  return date.toLocaleDateString(locale === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric',
    month: style === 'long' ? 'long' : 'short',
    day: 'numeric'
  })
}
```

Migrate call sites one file at a time, screenshotting each in **both locales**. Consolidation
is where a "pure refactor" silently changes what five screens display.

### Don't report

Two helpers sharing a name but genuinely doing different jobs (`getStockStatusClass` on a
list row vs. on a detail panel with different thresholds). Same name, different domain — merging
them is worse than leaving them.

---

## 4. Repeated data-loading scaffolding

Every view repeats: `loading` ref, `error` ref, `try/catch/finally`, `onMounted(load)`,
`watch(filters, load)`.

### Detect

```bash
grep -rn "watch(\[" views/*.vue
grep -c "loading.value = true" views/*.vue
```

### Confirm

Read two of the `load*` functions. If the only differences are the API method and the target
ref, it's extractable.

### Fix

```js
// composables/useFilteredResource.js
import { ref, onMounted, watch } from 'vue'
import { useFilters } from './useFilters'

// Wraps the load/loading/error/refetch-on-filter-change cycle every view repeats.
// `watchSources` is explicit because views watch different filter subsets - Inventory
// ignores period and status, Dashboard watches all four.
export function useFilteredResource(fetcher, watchSources) {
  const data = ref(null)
  const loading = ref(true)
  const error = ref(null)
  const { getCurrentFilters } = useFilters()

  const load = async () => {
    try {
      loading.value = true
      error.value = null
      data.value = await fetcher(getCurrentFilters())
    } catch (err) {
      error.value = 'Failed to load data'
      console.error('Load error:', err)
    } finally {
      loading.value = false
    }
  }

  onMounted(load)
  watch(watchSources, load)

  return { data, loading, error, reload: load }
}
```

Migrate **one view first** (`Inventory.vue` — the simplest), verify, then continue. Views with
extra state (`Restocking.vue` debounces a budget slider and seeds an initial value; `Dashboard.vue`
loads several resources) may keep their own loader — forcing them through the composable is
how a reuse win turns into a regression.

### Don't report

A view that only *looks* similar but has meaningfully different lifecycle needs. Note it as
"intentionally excluded" so the next audit doesn't re-flag it.

---

## 5. Extractable component shells

### Detect

```bash
grep -l "modal-overlay" components/*.vue
grep -c "^\.modal" components/*.vue     # duplicated CSS block count per file
```

### Confirm

Compare the outer markup of two candidates. Extract only if the overlay, close button,
escape handling, and container CSS match.

### Fix

`BaseModal.vue` with slots, keeping each modal's body as-is:

```vue
<!-- components/BaseModal.vue -->
<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal" role="dialog" aria-modal="true">
      <div class="modal-header">
        <h3 class="modal-title">{{ title }}</h3>
        <button class="modal-close" @click="$emit('close')" :aria-label="closeLabel">…</button>
      </div>
      <div class="modal-body"><slot /></div>
      <div v-if="$slots.footer" class="modal-footer"><slot name="footer" /></div>
    </div>
  </div>
</template>
```

Highest line savings in the codebase and the **highest blast radius** — six modals, all
reachable from different screens. Do it last, one modal per commit, screenshotting each.

### Don't report

Two components that merely both have a border and a heading. Shell extraction pays off at
five-plus near-identical instances, not two.

---

## 6. Documented-rule violations

Cheap to detect, already agreed to be wrong — `CLAUDE.md` Common Issues lists them.

```bash
grep -rn ':key="index\|:key="i"' views components     # rule 1
grep -rn "new Date(" views components | grep -v "isNaN\|if (!"   # rule 2, needs manual review
```

`:key="index"` fix: use the row's natural identity (`q.quarter`, `month.month`). If no unique
field exists, that's worth flagging on its own — the data shape is the real problem.
