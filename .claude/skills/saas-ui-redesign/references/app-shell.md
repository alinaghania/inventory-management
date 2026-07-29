# App shell

Three new components in `client/src/components/`, plus a rewritten `App.vue` template.
The shell is two columns: a fixed sidebar and a scrolling content column with a sticky top bar.

```
┌──────────────┬─────────────────────────────────────────┐
│ brand        │                              user ▾     │  ← AppTopbar (sticky, 64px)
│              ├─────────────────────────────────────────┤
│ ▎Overview    │ FilterBar (slim toolbar)                │
│  Inventory   ├─────────────────────────────────────────┤
│  Orders      │                                         │
│  Finance     │   existing view content, restyled       │
│  Demand      │                                         │
│  Reports     │                                         │
│              │                                         │
├──────────────┤                                         │
│  globe  EN   │                                         │  ← LanguageSwitcher
└──────────────┴─────────────────────────────────────────┘
     272px
```

The sidebar and the top bar are the only new markup. Everything to the right of the sidebar
is the app's current views with new CSS.

## AppIcon.vue

One component, a path map, no dependency. Every icon in the redesign comes from here.
Add cases as needed rather than inlining SVG in views.

```vue
<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path v-for="(d, i) in paths" :key="d" :d="d" />
  </svg>
</template>

<script>
import { computed } from 'vue'

// Each entry is a list of path `d` strings drawn with a shared stroke style.
const ICONS = {
  overview:  ['M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z'],
  inventory: ['M3 5h18v14H3z', 'M3 9h18', 'M9 13h6'],
  orders:    ['M6 6h15l-1.5 8h-12z', 'M6 6L5 3H2', 'M9 20a1 1 0 100-2 1 1 0 000 2z', 'M18 20a1 1 0 100-2 1 1 0 000 2z'],
  finance:   ['M2 6h20v12H2z', 'M2 10h20', 'M6 15h4'],
  demand:    ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'],
  reports:   ['M4 20V10', 'M10 20V4', 'M16 20v-7', 'M22 20H2'],
  truck:     ['M3 6h11v10H3z', 'M14 9h4l3 3v4h-7z', 'M7.5 19a1.5 1.5 0 100-3 1.5 1.5 0 000 3z', 'M17.5 19a1.5 1.5 0 100-3 1.5 1.5 0 000 3z'],
  // Below are used only if the user opts into KPI icon tiles (see view-styling.md)
  alert:     ['M12 3l9 16H3z', 'M12 9v5', 'M12 17h.01'],
  calendar:  ['M4 6h16v15H4z', 'M4 10h16', 'M9 3v4', 'M15 3v4'],
  check:     ['M4 5h13v15H4z', 'M8 12l3 3 5-5']
}

export default {
  name: 'AppIcon',
  props: {
    name: { type: String, required: true },
    size: { type: [Number, String], default: 20 }
  },
  setup(props) {
    // Unknown names render nothing rather than throwing — keeps a typo from blanking a page.
    const paths = computed(() => ICONS[props.name] || [])
    return { paths }
  }
}
</script>
```

## AppSidebar.vue

Nav items are data, not markup — one source of truth for path, i18n key, and icon.
Active state is computed rather than left to `router-link-active`, because `/` would
otherwise match every route.

```vue
<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <h1>{{ t('nav.companyName') }}</h1>
      <span>{{ t('nav.subtitle') }}</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <AppIcon :name="item.icon" :size="20" />
        <span>{{ t(item.labelKey) }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <LanguageSwitcher />
    </div>
  </aside>
</template>

<script>
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import AppIcon from './AppIcon.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

const NAV_ITEMS = [
  { path: '/',          labelKey: 'nav.overview',       icon: 'overview' },
  { path: '/inventory', labelKey: 'nav.inventory',      icon: 'inventory' },
  { path: '/orders',    labelKey: 'nav.orders',         icon: 'orders' },
  { path: '/spending',  labelKey: 'nav.finance',        icon: 'finance' },
  { path: '/demand',    labelKey: 'nav.demandForecast', icon: 'demand' },
  { path: '/reports',   labelKey: 'nav.reports',        icon: 'reports' }
  // `/restocking` is a registered route and `nav.restocking` is already translated in both
  // locales, but it is absent from the target design's six-item nav. Ask the user whether to
  // add a seventh item — a reachable route with no nav entry is a dead end now that the top
  // tabs are gone. If added, it sits after Orders and uses the `truck` icon.
]

export default {
  name: 'AppSidebar',
  components: { AppIcon, LanguageSwitcher },
  setup() {
    const { t } = useI18n()
    const route = useRoute()

    // '/' must match exactly; every other route also matches its sub-paths.
    const isActive = (path) =>
      path === '/' ? route.path === '/' : route.path.startsWith(path)

    return { t, navItems: NAV_ITEMS, isActive }
  }
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-w);
  height: 100vh;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.sidebar-brand { padding: var(--space-6) var(--space-5) var(--space-5); }

.sidebar-brand h1 {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.15;
  color: var(--brand-900);
  letter-spacing: var(--tracking-tight);
}

.sidebar-brand span {
  display: block;
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0.625rem var(--space-3);
  border-radius: var(--radius-md);
  color: var(--text-body);
  text-decoration: none;
  font-size: var(--text-base);
  font-weight: 500;
  /* Transparent bar reserves the space so active items don't shift horizontally */
  border-left: 3px solid transparent;
  transition: background var(--transition), color var(--transition);
}

.nav-item svg { color: var(--text-faint); flex-shrink: 0; transition: color var(--transition); }

.nav-item:hover { background: var(--surface-muted); color: var(--text); }
.nav-item:hover svg { color: var(--text-muted); }

.nav-item.active {
  background: var(--brand-100);
  border-left-color: var(--brand-900);
  color: var(--brand-900);
  font-weight: 600;
}

.nav-item.active svg { color: var(--brand-900); }

.sidebar-footer {
  padding: var(--space-4) var(--space-3);
  border-top: 1px solid var(--border);
}
</style>
```

**LanguageSwitcher adjustment:** its dropdown currently opens downward. In the sidebar
footer it must open upward — add `bottom: 100%` positioning to `.dropdown-menu` within
that component's scoped styles. Its globe icon and label already match the target look.

## AppTopbar.vue

The top bar exists because `ProfileMenu` needs a home once the top nav is gone. It holds
**only what the app already has** — no search field, no notification bell, no settings gear.
Those appear in the reference design but are non-functional chrome; adding them would be a
feature, not a restyle.

`ProfileMenu` keeps its existing two emits, re-emitted here so `App.vue`'s handlers stay
unchanged.

```vue
<template>
  <header class="topbar">
    <div class="topbar-actions">
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </header>
</template>

<script>
import ProfileMenu from './ProfileMenu.vue'

export default {
  name: 'AppTopbar',
  components: { ProfileMenu },
  emits: ['show-profile-details', 'show-tasks']
}
</script>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  gap: var(--space-4);
  height: var(--topbar-h);
  padding: 0 var(--space-8);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.topbar-actions { margin-left: auto; display: flex; align-items: center; gap: var(--space-2); }
</style>
```

**ProfileMenu restyle:** the reference design sets the role line small, uppercase, and muted
beneath the name — `font-size: var(--text-xs); letter-spacing: var(--tracking-wide);
text-transform: uppercase; color: var(--text-muted)`. Apply that to whatever elements
`ProfileMenu` already renders. Do not add or remove anything from its trigger, and leave its
dropdown logic and emits alone.

## App.vue template

Only the template and shell CSS change. Everything in `setup()` — tasks, modals, `useAuth`,
`useI18n` — stays exactly as it is.

```vue
<template>
  <div class="app">
    <AppSidebar />

    <div class="app-main">
      <AppTopbar
        @show-profile-details="showProfileDetails = true"
        @show-tasks="showTasks = true"
      />
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal :is-open="showProfileDetails" @close="showProfileDetails = false" />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>
```

Shell rules for the global `<style>` block, appended after the tokens:

```css
.app { min-height: 100vh; }

/* Sidebar is fixed, so the content column is offset rather than laid out beside it */
.app-main {
  margin-left: var(--sidebar-w);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  padding: var(--space-6) var(--space-8) var(--space-10);
}
```

`ProfileMenu` is no longer a direct child of `App.vue` — remove its import and component
registration there, and remove the `.nav-container > .language-switcher` and
`.nav-container > .nav-tabs` rules.

## i18n keys

Existing `nav.*` keys already cover five of the six sidebar items: `nav.overview`,
`nav.inventory`, `nav.orders`, `nav.finance`, `nav.demandForecast`. Only Reports is missing.

`nav.companyName` is already `Catalyst Components` and needs no change — the wordmark wraps
to two lines at 272px, which is the intended look. `nav.subtitle` is
`Inventory Management System`; the reference design shows different words there, but that is
copy, not style. Leave it.

Exactly **one** key is missing, because "Reports" is hardcoded in `App.vue` today. Add it to
both locales:

| Key | en | ja |
| --- | --- | --- |
| `nav.reports` | Reports | レポート |

After adding it, switch the app to Japanese and confirm no sidebar item wraps to a second
line at 272px.
