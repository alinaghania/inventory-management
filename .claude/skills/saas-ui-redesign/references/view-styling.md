# View styling

How to restyle the existing views. **Nothing here adds UI.** Each rule is either a class
swap, a spacing correction, or a CSS change — the rendered information stays identical.

Before editing a view, screenshot it. After editing, screenshot again and diff the two. Same
numbers, same rows, same controls, better looking.

## What actually changes in a view file

Most views need very little, because step 1's token layer already restyled `.card`,
`.stat-card`, `.badge`, `.page-header`, and `table` from underneath them. Typical edits:

1. **Remove hardcoded colors and spacing.** Scoped `<style>` blocks in views repeat literals
   like `#64748b`, `1.25rem`, `10px`. Replace with `var(--text-muted)`, `var(--space-5)`,
   `var(--radius-lg)`. This is the bulk of the work and it is purely mechanical.
2. **Delete scoped rules that now duplicate the global layer.** If a view restyles `.card`
   or `.badge` locally with the same intent, drop the local rule and let the token layer win.
3. **Normalize section spacing** to `var(--space-6)` between major blocks and
   `var(--space-5)` between cards. Inconsistent gaps are the main reason the current UI
   reads as unpolished.
4. **Apply `.num` to numeric table columns** so digits align. Class only, no markup change.

## Optional: KPI icon tiles

The one *additive* change worth considering, because it carries most of the SaaS look. It
adds a decorative icon to each `.stat-card` — no data, no logic.

```vue
<div class="stat-card success">
  <div class="stat-top">
    <span class="stat-icon"><AppIcon name="check" :size="20" /></span>
  </div>
  <div class="stat-label">{{ t('...') }}</div>
  <div class="stat-value">{{ ... }}</div>
</div>
```

Note the modifier class (`success` / `warning` / `danger` / `info`) now tints the **icon
tile** rather than the number, so a row of KPIs reads as one scale instead of a traffic
light. Values stay near-black.

Cards look correct without `.stat-top` too — the token layer doesn't require it. Ask the
user before adding icon tiles, and if you add them, add them to every KPI card in the app
rather than a few.

Icon suggestions: `check` (value/assets), `alert` (low stock), `truck` (orders/restocking),
`calendar` (period metrics), `demand` (growth), `finance` (spend).

## Tables

Add to the global block:

```css
th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; }
```

Apply `.num` to quantity, cost, and value columns. Add `white-space: nowrap` to identifier
columns (SKU, dates) so they don't wrap to two lines.

Keep every column that exists today. The inventory table's nine columns are tight in the
narrower content area — if one scrolls horizontally, that is acceptable and
`.table-container` already handles it. Do not merge or drop columns to make it fit.

Badges keep their existing classes and existing logic. The token layer restyles
`success` / `warning` / `danger` / `info` / `increasing` / `decreasing` / `stable` /
`high` / `medium` / `low` in place — no view needs to change which class it emits.

## FilterBar as a toolbar

Presentation only. `useFilters` bindings, the four selects, and the reset button all stay.

- Drop the stacked `label` above each select; fold it into the select as a disabled first
  option so no text is lost.
- Row height ~52px, horizontally scrollable on narrow viewports,
  `border-bottom: 1px solid var(--border)`, `background: var(--surface)`.
- Match the content column's horizontal padding (`var(--space-8)`) so controls line up with
  the page content below.
- Style each `.filter-select` as a bordered pill: `var(--radius-md)`, `1px solid
  var(--border)`, `var(--text-sm)`, white background.
- The reset button becomes an `.icon-btn` right-aligned via `margin-left: auto`, keeping its
  existing `:disabled="!hasActiveFilters"` binding and `title` attribute.

## Panel headers

Existing `.card-header` markup (title on the left, whatever the view already puts on the
right) works as-is. The token layer moves the header to an inset bar with a bottom border
and lets the body reach the panel edges, so tables bleed full-width.

If a view's panel header currently has nothing on the right, leave it empty. Do not fill it.

## Per-view notes

| View | Notes |
| --- | --- |
| `Inventory.vue` | Start here. Table-plus-KPIs, the pattern most views follow. |
| `Orders.vue` | Status badges already map to `delivered`/`shipped`/`processing`/`backordered`. No logic change. |
| `Spending.vue` | Labeled **Finance** in nav; the page's own title stays whatever it is today. Currency stays on `utils/currency.js`. |
| `Demand.vue` | Uses `increasing`/`decreasing`/`stable` badges, already covered by the token layer. |
| `Reports.vue` | Nav label is hardcoded today — this is where `nav.reports` gets used, in the sidebar, not the page. |
| `Restocking.vue` | Recently added and may still be changing. Re-read before editing. |
| `Dashboard.vue` | Last, and most careful. 1271 lines with hand-rolled SVG charts. Restyle card containers, headers, and legends only — leave every `<path>`/`<rect>` coordinate calculation alone, then verify charts still fit after the sidebar narrows the content column. |
| `Backlog.vue` | No route. Leave untouched. |

## Width check

The sidebar takes 272px from a 1280px viewport, leaving 1008px minus 64px padding for
content — about 944px, down from roughly 1216px today. Every view gets meaningfully
narrower.

Check each one after the shell lands. Charts in `Dashboard.vue` are the main risk, since
their SVG widths may be hardcoded. Prefer making a chart responsive over removing content.
