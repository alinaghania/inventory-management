---
name: vue-component-audit
description: Analyzes Vue 3 component structure in client/src and reports prioritized optimizations for render performance and code reuse — uncached template methods, duplicated helpers that have drifted, repeated data-loading scaffolding, and extractable component shells. Produces a findings report, not edits, unless asked to fix. Use when asked to audit, analyze, review, optimize, refactor, or find duplication in Vue components, or when a view feels slow or bloated.
---

# Vue Component Audit

Analyzes `client/src` and reports **prioritized, verified** optimizations for render
performance and code reuse.

## Output contract: report first, edit only on request

Default output is a findings report. Do **not** start editing `.vue` files because the audit
found something — the ranked report *is* the deliverable. Only implement when the user asks
for fixes, and then implement the specific findings they picked, not everything.

Why this matters: several findings below are one-line detections with multi-file fixes. A
"helpful" unprompted refactor across six modals is exactly the change nobody asked for.

## Every finding needs a failure, not a smell

A finding that says "this could be a computed property" is noise. State what it *costs*:

> `Orders.vue:14-26` calls `getOrdersByStatus()` four times in the template. It's a method,
> not a computed, so each call re-scans the full orders array on **every** render — 4 full
> passes per keystroke in any filter input. Fix: four computeds, or one computed returning
> counts grouped by status.

Rank by **impact ÷ effort**, and say which files each fix touches. A finding the user can't
price is a finding they'll skip.

## What to analyze

Run the detections in `references/patterns.md`. They cover four categories:

| Category | Looks for |
| --- | --- |
| **Uncached render work** | Methods called from templates, work inside `v-for`, composables invoked per-call |
| **Drifted duplication** | Same-named helpers in N files whose behavior has silently diverged |
| **Scaffolding repetition** | Identical `loading`/`error`/`watch(filters)`/`onMounted` blocks across views |
| **Extractable structure** | Repeated markup + CSS shells (modals, tables, stat cards) |

`references/baseline-findings.md` is a **verified inventory of what is already wrong in this
repo**, with exact line numbers. Read it before analyzing so you report new findings and
confirm-or-clear old ones, rather than rediscovering the same six `formatDate` copies and
presenting them as fresh.

Re-verify before reporting. That file was accurate when written; this repo has frequent
uncommitted work in progress. Run `git status` first, and confirm each finding still exists
at the stated line before repeating it.

## Priority order

Rank findings in this order, because it maps to impact per unit of risk:

1. **Correctness bugs the duplication is hiding.** Drifted copies aren't just ugly — three of
   the six `formatDate` variants hardcode `'en-US'` and ignore Japanese locale. That's a live
   i18n bug wearing a DRY costume. Lead with these.
2. **Uncached work in hot paths.** Template methods over arrays, recomputed per render.
3. **Documented-rule violations.** `:key="index"` is called out in `CLAUDE.md` Common Issues
   and still ships in `Reports.vue`.
4. **Scaffolding extraction.** High line-count savings, mechanical, low risk.
5. **Component shell extraction.** Highest savings, highest blast radius — last.

## False positives to suppress

Do not report these. They are the noise that makes audits get ignored:

| Not a finding | Why |
| --- | --- |
| A parameterized method used **once** in a template | A computed can't take an argument without becoming a factory; one call isn't worth it |
| `translateProductName(item.name)` in a `v-for` | It's a dictionary lookup, not a scan. Cheap and correct |
| Any `v-memo` suggestion | This app's lists are tens of rows. `v-memo` adds correctness risk for unmeasurable gain |
| `shallowRef` / `markRaw` / `Object.freeze` micro-tuning | Premature at this data size |
| "Split this component" based on line count alone | `Dashboard.vue` is 1271 lines because it renders eight panels. Only recommend splitting where a panel is genuinely reusable elsewhere |
| Missing `key` on a static, never-reordered list | Real but inert |
| Suggesting a state library, a component library, or any new dependency | See constraints |

If a check fires but you can't name a concrete cost, drop it. Under-reporting beats a report
the user has to filter.

## Repo constraints the recommendations must respect

From `CLAUDE.md` and `client/CLAUDE.md` — a recommendation violating one of these is invalid,
however clean it looks:

1. **Three runtime dependencies:** `vue`, `vue-router`, `axios`. Never recommend adding one —
   that includes `@vueuse/core`, even though `client/CLAUDE.md` shows a `watchDebounced`
   example. Hand-roll it, as `Restocking.vue` already does.
2. **Composition API only.** Never mix in Options API.
3. **i18n strings live in both `en.js` and `ja.js`.** An extraction that consolidates strings
   must keep both locales in sync.
4. **No emojis in UI.** Icons are inline SVG.
5. **Unique `v-for` keys** — `sku`, `month`, `path`. Never `index`.
6. **No test framework exists on the client.** Don't propose a fix whose safety net is
   "the component tests will catch it." Verification is `npm run build` plus Playwright MCP.
7. **`.vue` edits delegate to `vue-expert`** via the Task tool, per `CLAUDE.md`. Audit
   findings are the spec you hand that agent. (Analysis itself is read-only — no delegation
   needed to produce the report.)

## Method

```bash
cd client && npm run build   # must be green before and after any fix
```

1. `git status` — know what's uncommitted before attributing anything.
2. Read `references/baseline-findings.md`.
3. Run the detections in `references/patterns.md` across `views/`, `components/`,
   `composables/`.
4. For each hit: open the file, confirm it's real, and write down the concrete cost.
5. Drop everything matching the false-positive table.
6. Rank by the priority order above.
7. Report.

## Report format

```markdown
## Vue component audit — <N> findings

### 1. <Finding> — <files touched>
**Cost:** <the concrete failure or waste, with numbers where possible>
**Where:** `path/file.vue:LINE` (+ N other sites)
**Fix:** <specific change, 1-3 sentences>
**Effort:** S | M | L    **Risk:** low | medium | high
```

Close with a one-line total: how many lines the reuse findings would remove, and which
single finding to do first.

## Verification, when fixes are requested

- `npm run build` succeeds.
- Playwright MCP screenshot of every affected route, compared against pre-change shots.
  **Same information on screen** — a refactor that drops a column is a regression.
- Toggle to Japanese and re-check any view touched by a formatter or i18n consolidation.
  This is where consolidating drifted helpers actually breaks things: the surviving
  implementation must handle every case its siblings did, including their null returns
  (`'-'`, `'N/A'`, and `''` are all in use today).

## Reference files

- `references/patterns.md` — detection commands, fix recipes, false-positive guards.
- `references/baseline-findings.md` — verified current-state inventory with line numbers.
