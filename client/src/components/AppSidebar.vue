<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <!-- Decorative mascot: the wordmark beside it already names the product -->
      <img class="brand-mascot float" src="/mascot.png" alt="" width="56" height="56">
      <div class="brand-text">
        <h1>{{ t('nav.companyName') }}</h1>
        <span>{{ t('nav.subtitle') }}</span>
      </div>
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

// Single source of truth for path, label key, and icon. Mirrors the routes in main.js.
const NAV_ITEMS = [
  { path: '/', labelKey: 'nav.overview', icon: 'overview' },
  { path: '/inventory', labelKey: 'nav.inventory', icon: 'inventory' },
  { path: '/orders', labelKey: 'nav.orders', icon: 'orders' },
  { path: '/spending', labelKey: 'nav.finance', icon: 'finance' },
  { path: '/demand', labelKey: 'nav.demandForecast', icon: 'demand' },
  { path: '/restocking', labelKey: 'nav.restocking', icon: 'restocking' },
  { path: '/reports', labelKey: 'nav.reports', icon: 'reports' }
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

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5);
  border-bottom: 1px solid var(--border);
}

.brand-mascot {
  flex-shrink: 0;
}

.brand-text {
  min-width: 0;
}

/* Serif wordmark, small caps — the masthead of the page */
.sidebar-brand h1 {
  font-family: var(--font-serif);
  font-size: 1.25rem;
  font-weight: 800;
  line-height: 1.15;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Gold eyebrow under the wordmark, matching the KPI labels */
.sidebar-brand span {
  display: block;
  margin-top: 3px;
  font-size: 9.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--gold);
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0.5rem var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  text-decoration: none;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  transition: background var(--transition), color var(--transition);
}

.nav-item svg {
  color: var(--text-faint);
  flex-shrink: 0;
  transition: color var(--transition);
}

.nav-item:hover {
  background: var(--surface-muted);
  color: var(--text);
}

.nav-item:hover svg {
  color: var(--text);
}

/* Active state is a solid ink block — no rule, no bar, just the fill */
.nav-item.active {
  background: var(--brand-900);
  color: #ffffff;
}

.nav-item.active:hover {
  background: var(--brand-700);
  color: #ffffff;
}

.nav-item.active svg,
.nav-item.active:hover svg {
  color: #ffffff;
}

.sidebar-footer {
  padding: var(--space-4) var(--space-3);
  border-top: 1px solid var(--border);
}
</style>
