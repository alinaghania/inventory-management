# Baseline findings — verified inventory

Snapshot of what was already wrong in `client/src` when this skill was written, so an audit
reports *new* findings instead of rediscovering these.

**Re-verify before repeating any of it.** This repo frequently carries uncommitted work and
line numbers move. Run `git status`, then confirm each item still exists at the stated line.
Mark anything already fixed as resolved rather than re-reporting it.

Counts at snapshot time: 8,265 lines across `views/`, `components/`, `composables/`, `utils/`.

---

## B1 — Six `formatDate` copies, drifted three ways (correctness)

| File | Line | Null input | Locale | Format |
| --- | --- | --- | --- | --- |
| `views/Dashboard.vue` | 635 | `'-'` | respects `ja` | short + year |
| `views/Orders.vue` | 202 | *unguarded* | respects `ja` | short + year |
| `views/Spending.vue` | 396 | *unguarded* | **hardcoded `en-US`** | short, no year |
| `components/ProfileDetailsModal.vue` | 88 | *unguarded* | respects `ja` | long + year |
| `components/ProductDetailModal.vue` | 115 | `'N/A'` | **hardcoded `en-US`** | long + year |
| `components/BacklogDetailModal.vue` | 115 | `'N/A'` | **hardcoded `en-US`** | long + year |

Three findings in one:

1. **Live i18n bug.** Three sites hardcode `'en-US'`. Switch the app to Japanese and those
   dates stay English. This is a user-visible defect, not a style issue — report it as such.
2. **Three different empty-value placeholders** (`'-'`, `'N/A'`, unguarded). Any consolidation
   must parameterize this or it silently changes what five screens render.
3. **Three unguarded sites** render `Invalid Date` for malformed input — the exact hazard
   `CLAUDE.md` Common Issue #2 warns about.

Fix recipe: `patterns.md` §3.

---

## B2 — Uncached template scans (performance)

- `views/Orders.vue:14-26` — `getOrdersByStatus()` called 4× in the template; defined as a
  plain method at line 188 (`orders.value.filter(...)`). **4 full array scans per render.**
- `views/Backlog.vue:14-22` — `getBacklogByPriority()` called 3×; defined at line 133.
  **3 full scans per render.** (Note: `Backlog.vue` has no route registered in `main.js`, so
  this is currently unreachable — lower its priority accordingly, don't drop it.)

Fix recipe: `patterns.md` §1, "fixed set of arguments" variant.

---

## B3 — `useI18n()` called per invocation (performance)

Called inside function bodies rather than `setup()` scope:

- `views/Dashboard.vue:637` — inside `formatDate`, which runs per row of the top-products table
- `views/Orders.vue:203` — inside `formatDate`
- `views/Demand.vue:194` — inside `translatePeriod`, called per forecast row

Fix recipe: `patterns.md` §2. Low risk, mechanical.

---

## B4 — `:key="index"` (documented-rule violation)

`views/Reports.vue` lines **28**, **51**, **82**.

Explicitly listed as Common Issue #1 in `CLAUDE.md`. Natural keys are available —
`q.quarter` and `month.month`.

---

## B5 — Duplicated `translate*` helpers (reuse)

- `translateCategory` — `views/Inventory.vue:188`, `views/Dashboard.vue:604`,
  `views/Spending.vue:429`
- `translatePriority` — `views/Dashboard.vue`, `components/TasksModal.vue`
- `getStockStatusClass` — `views/Inventory.vue`, `components/InventoryDetailModal.vue`
  (**check before merging** — the detail modal's version takes no argument and reads
  component state; these may be genuinely different functions sharing a name)

---

## B6 — Repeated load scaffolding (reuse)

Seven views each hand-roll `loading` + `error` + `try/catch/finally` + `onMounted` +
`watch(filters)`:

| View | Loader | Watches |
| --- | --- | --- |
| `Inventory.vue` | `loadInventory` :152 | location, category |
| `Demand.vue` | `loadForecasts` :142 | location, category |
| `Backlog.vue` | `loadBacklog` :111 | location, category |
| `Orders.vue` | `loadOrders` :156 | all four |
| `Dashboard.vue` | `loadData` :561 | all four |
| `Spending.vue` | `loadData` :350 | period only |
| `Restocking.vue` | `loadRecommendations` :288 | location, category |

The watch subsets genuinely differ — any composable must take them as a parameter.

**Exclude `Restocking.vue`** from the first pass: it debounces the budget slider, seeds an
initial budget from a probe request, and suppresses its own watcher during seeding. Forcing
it through a generic composable would break that sequence. `Dashboard.vue` loads several
resources in one call and also needs care.

Fix recipe: `patterns.md` §4. Start with `Inventory.vue`.

---

## B7 — Six modals sharing a shell (reuse, highest savings)

`TasksModal` (621), `InventoryDetailModal` (450), `CostDetailModal` (384),
`BacklogDetailModal` (380), `ProductDetailModal` (335), `ProfileDetailsModal` (280).

Each carries **14 duplicated `.modal*` CSS blocks** plus its own overlay, close button, and
escape handling.

Largest single reuse win available and the largest blast radius. Do it last, one modal per
commit. Fix recipe: `patterns.md` §5.

---

## Deliberately not findings

Recorded so each audit doesn't re-litigate them:

- **`Dashboard.vue` is 1271 lines.** It renders eight distinct panels. Size alone isn't a
  defect; only recommend splitting a panel that's genuinely reusable elsewhere.
- **`views/Backlog.vue` has no route** in `main.js`. Known dead view — leave it alone, and
  discount the priority of findings inside it.
- **No client test framework.** Don't propose fixes justified by "tests will catch it."
  Verification is `npm run build` plus Playwright MCP screenshots.
- **`Restocking.vue`'s hand-rolled debounce** (`BUDGET_DEBOUNCE_MS`). Correct given the
  three-dependency constraint — do not suggest `@vueuse/core`.
