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
  padding: var(--space-6) var(--space-5) var(--space-5);
}

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
  color: var(--text-muted);
}

.nav-item.active {
  background: var(--brand-100);
  border-left-color: var(--brand-900);
  color: var(--brand-900);
  font-weight: 600;
}

.nav-item.active svg {
  color: var(--brand-900);
}

.sidebar-footer {
  padding: var(--space-4) var(--space-3);
  border-top: 1px solid var(--border);
}
</style>
