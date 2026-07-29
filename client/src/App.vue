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

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

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

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import AppSidebar from './components/AppSidebar.vue'
import AppTopbar from './components/AppTopbar.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'

export default {
  name: 'App',
  components: {
    AppSidebar,
    AppTopbar,
    FilterBar,
    ProfileDetailsModal,
    TasksModal
  },
  setup() {
    const { currentUser } = useAuth()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* ============================================================================
   Design tokens + primitives.
   Utility class names are unchanged from the previous stylesheet, so every view
   picks up the new look without being edited.
   ============================================================================ */

:root {
  /* Brand — deep forest green. Wordmark, active nav, primary actions. */
  --brand-900: #14532d;
  --brand-700: #166534;
  --brand-500: #22c55e;
  --brand-100: #dcfce7;
  --brand-50: #f0fdf4;

  /* Neutrals */
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-muted: #f8fafc;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #0f172a;
  --text-body: #334155;
  --text-muted: #64748b;
  --text-faint: #94a3b8;

  /* Status — tinted surface + readable foreground, one pair per state */
  --success-bg: #dcfce7;
  --success-fg: #065f46;
  --warning-bg: #fef3c7;
  --warning-fg: #92400e;
  --danger-bg: #fee2e2;
  --danger-fg: #991b1b;
  --info-bg: #dbeafe;
  --info-fg: #1e40af;

  /* Spacing — 4px base */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-pill: 999px;

  /* Elevation — deliberately shallow; borders carry most of the separation */
  --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);

  /* Type */
  --text-xs: 0.6875rem;
  --text-sm: 0.8125rem;
  --text-base: 0.875rem;
  --text-md: 0.9375rem;
  --text-lg: 1.0625rem;
  --text-2xl: 1.75rem;
  --text-3xl: 1.875rem;

  --tracking-tight: -0.02em;
  --tracking-wide: 0.06em;

  /* Shell geometry */
  --sidebar-w: 272px;
  --topbar-h: 64px;
  --content-max: 1440px;

  --transition: 0.15s ease;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--bg);
  color: var(--text-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* --- Shell ---------------------------------------------------------------- */

.app {
  min-height: 100vh;
}

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

/* --- Page header ---------------------------------------------------------- */

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text);
  margin-bottom: var(--space-2);
  letter-spacing: var(--tracking-tight);
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-md);
}

/* --- Buttons -------------------------------------------------------------- */
/* For restyling buttons the app already has. This redesign adds no new buttons. */

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0.5625rem var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: 600;
  font-family: inherit;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background var(--transition), border-color var(--transition);
  white-space: nowrap;
}

.btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.btn-primary {
  background: var(--brand-900);
  color: #fff;
}

.btn-primary:hover {
  background: var(--brand-700);
}

.btn-secondary {
  background: var(--surface);
  color: var(--text-body);
  border-color: var(--border);
  box-shadow: var(--shadow-xs);
}

.btn-secondary:hover {
  background: var(--surface-muted);
  border-color: var(--border-strong);
}

/* Square icon-only button — used by FilterBar's existing reset control */
.icon-btn {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  cursor: pointer;
  transition: background var(--transition), color var(--transition);
}

.icon-btn svg {
  width: 18px;
  height: 18px;
}

.icon-btn:hover:not(:disabled) {
  background: var(--surface-muted);
  color: var(--text);
}

.icon-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

/* --- KPI cards ------------------------------------------------------------ */

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  transition: border-color var(--transition), box-shadow var(--transition);
}

.stat-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  margin-bottom: var(--space-2);
}

/* Value stays neutral so a row of KPIs reads as one scale, not a traffic light */
.stat-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text);
  letter-spacing: var(--tracking-tight);
}

/* --- Panels --------------------------------------------------------------- */

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text);
  letter-spacing: var(--tracking-tight);
}

/* --- Tables --------------------------------------------------------------- */

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--surface-muted);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: var(--space-3);
  font-weight: 600;
  color: var(--text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  white-space: nowrap;
}

td {
  padding: var(--space-3);
  border-top: 1px solid #f1f5f9;
  color: var(--text-body);
  font-size: var(--text-base);
}

tbody tr {
  transition: background-color var(--transition);
}

tbody tr:hover {
  background: var(--surface-muted);
}

/* Right-align numeric columns so digits line up down the column */
th.num,
td.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* --- Badges --------------------------------------------------------------- */

.badge {
  display: inline-block;
  padding: 0.25rem var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

/* Every badge class the views already emit is covered here — no view needs to
   change which class it renders. */
.badge.success,
.badge.increasing {
  background: var(--success-bg);
  color: var(--success-fg);
}

.badge.warning,
.badge.medium {
  background: var(--warning-bg);
  color: var(--warning-fg);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--danger-bg);
  color: var(--danger-fg);
}

.badge.info,
.badge.low {
  background: var(--info-bg);
  color: var(--info-fg);
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

/* --- States --------------------------------------------------------------- */

.loading {
  text-align: center;
  padding: var(--space-10);
  color: var(--text-muted);
  font-size: var(--text-md);
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: var(--danger-fg);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-md);
}
</style>
