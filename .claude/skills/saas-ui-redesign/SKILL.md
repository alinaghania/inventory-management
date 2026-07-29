---
name: saas-ui-redesign
description: Restyles the Vue 3 client into a modern SaaS look — left vertical navigation sidebar replacing the top nav bar, a shared design-token layer, and consistent spacing across every view. Presentation only, no feature changes. Use when asked to redesign or modernize the UI, move navigation to a sidebar, apply consistent spacing, or make the app look polished and professional.
---

# SaaS UI Redesign

Restyles `client/` to look like a modern SaaS product: a fixed left sidebar replacing the
top nav tabs, one spacing and color system, and polished surfaces across all views.

## Scope: style only

**This skill changes how the app looks, never what it does.** Every screen keeps exactly the
same content, controls, and behavior it has today — only the visual language changes.

The one structural change is navigation: the top tab bar becomes a left sidebar. That is
what the user asked for. Everything else is CSS, tokens, and spacing.

Do **not** add, as part of this work:

| Don't add | Why |
| --- | --- |
| Breadcrumbs | New navigation content |
| Page action buttons ("Export CSV", "New SKU") | New features; no matching API routes exist |
| Search inputs — global or per-panel | New feature |
| KPI trend badges ("+4.2%") | Would require inventing numbers not in the data |
| Filter chips duplicating `FilterBar` | Duplicate state |
| New/merged/removed table columns | Changes information architecture |
| New computed values, thresholds, or status logic | Behavior, not style |
| Copy rewrites, new page subtitles | Content |
| Dependencies, including icon libraries | Repo has three runtime deps; keep it that way |

If a reference design shows one of these, it is inspiration for *look*, not a list of
features to build. When something seems genuinely missing, mention it to the user and move
on — do not build it.

## Non-negotiables for this repo

From `CLAUDE.md`, and easy to violate during a visual pass:

1. **Delegate `.vue` work to `vue-expert`.** Any time you create or significantly modify a
   `.vue` file, delegate to the `vue-expert` subagent via the Task tool. This skill's
   reference files are the spec you hand that agent.
2. **No emojis in UI.** Icons are inline SVG.
3. **All user-facing strings go through i18n**, in **both** `en.js` and `ja.js`. This work
   needs exactly one new key — see `references/app-shell.md`.
4. **Unique `v-for` keys.** Use `sku`, `month`, `path` — never `index`.
5. **Do not touch data flow.** `useFilters`, `api.js`, and every computed property stay as
   they are. If a restyle seems to require changing filter state, stop and flag it.
6. **Comment non-obvious logic.** Matches existing house style.

## Preflight

```bash
cd client && npm run dev   # must boot clean on :3000
```

Run `git status` before planning. This repo frequently has uncommitted work in progress and
the route set moves with it — re-read `main.js` at the moment you build the nav list rather
than trusting an earlier reading.

Current state worth knowing:

- Routes: `/` (Overview), `/inventory`, `/orders`, `/spending` (labeled **Finance**),
  `/demand` (Demand Forecast), `/restocking`, `/reports`.
- `views/Backlog.vue` exists with **no route**. Leave it alone.
- Nav labels are already keyed: `nav.overview`, `nav.inventory`, `nav.orders`, `nav.finance`,
  `nav.demandForecast`, `nav.restocking`. Only "Reports" is hardcoded in `App.vue`.
- `App.vue` holds the entire global stylesheet in one unscoped `<style>` block
  (lines ~167–489). That block is the foundation for the token layer.

## Execution order

Each step leaves the app running, so verify with Playwright MCP against
`http://localhost:3000` between steps.

### 1. Token layer

Replace the top of `App.vue`'s global `<style>` with `references/design-tokens.css`.

This is the highest-leverage step and it edits no views. Keep every existing class name
(`.card`, `.badge`, `.stat-card`, `.page-header`, `table`, `.loading`, `.error`) and
rewrite only their internals against tokens. All seven views should look noticeably better
before a single view file is opened.

Delete only what the sidebar replaces: `.top-nav`, `.nav-container`, `.nav-tabs`, `.logo`,
`.subtitle`.

### 2. App shell

Build `AppSidebar.vue`, `AppTopbar.vue`, and `AppIcon.vue` in `client/src/components/`, then
rewrite `App.vue`'s **template** around them. Full markup and styles:
`references/app-shell.md`.

`App.vue`'s `setup()` is untouched — tasks, modals, `useAuth`, `useI18n` all stay. `ProfileMenu`
moves into the top bar, `LanguageSwitcher` into the sidebar footer; both keep their existing
props and emits, which continue to reach `App.vue`.

### 3. FilterBar

`FilterBar` keeps its `useFilters` bindings, its four selects, and its reset button. Only its
presentation changes — full-width band becomes a slim toolbar. See `references/view-styling.md`.

### 4. Views

Apply `references/view-styling.md` to `client/src/views/`. This is a restyling pass: adjust
classes and spacing, leave markup structure and logic alone.

Order: `Inventory.vue` first (simplest table view — get the language right there), then
`Orders.vue`, `Spending.vue`, `Demand.vue`, `Reports.vue`, `Restocking.vue`, and
`Dashboard.vue` last.

### 5. Modals

The six `*Modal.vue` components need token values applied to their surfaces, radii, and
padding so they match the new shell. Structure stays as-is.

## Verification

- `npm run build` succeeds.
- Playwright MCP screenshot of every route at 1280×1024.
- **Every route shows the same information it did before.** Compare against pre-change
  screenshots — a restyle that drops a column or a card is a regression, not a redesign.
- Toggle to Japanese, re-screenshot. Longer strings must not wrap or clip the 272px sidebar.
- Each route's active nav item is highlighted, and only that one.
- No horizontal scrollbar at 1280px on any route.

## Reference files

- `references/design-tokens.css` — token layer and restyled primitives. Paste-ready.
- `references/app-shell.md` — sidebar, top bar, icon component, new `App.vue` template.
- `references/view-styling.md` — how to restyle existing views without changing them.
