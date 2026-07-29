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
   Design tokens + primitives — editorial/monochrome language.

   The palette is near-monochrome (paper white, ink black, hairline grey) with a
   single gold accent reserved for eyebrow labels and focus. Separation comes
   from 1px rules, not shadows; radii are deliberately tiny so surfaces read as
   printed panels rather than floating cards.

   Every token name and every utility class name is unchanged from the previous
   stylesheet, so component scoped styles pick up the new look untouched.
   ============================================================================ */

:root {
  /* Type stacks — Geist for UI, Geist Mono for figures, Playfair for headings */
  --font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  --font-serif: 'Playfair Display', Georgia, 'Times New Roman', serif;

  /* Ink — the "brand" is black. Wordmark, active nav, primary actions. */
  --brand-900: #111111;
  --brand-700: #2b2b2b;
  --brand-500: #9c7c2e; /* gold — focus ring and eyebrow accent */
  --brand-100: #f2f2f2;
  --brand-50: #f7f7f7;

  /* The one chromatic note in the whole system */
  --gold: #9c7c2e;

  /* Chart series — a rose ramp borrowed from lotus-mobile (#ec4899 / #fce7f3).
     Charts are the only place this palette appears; status text and badges stay
     on the ink scale so meaning never rides on the decorative colour.
     Ordered for adjacency contrast, so neighbouring donut segments stay legible. */
  --chart-1: #ec4899;
  --chart-2: #9d174d;
  --chart-3: #f9a8d4;
  --chart-4: #db2777;
  --chart-5: #fbcfe8;
  --chart-track: #fce7f3;
  /* Flat wash for the accented rectangles (KPI/trend/priority cards). Filled
     blocks replace the old 4px left rules, which read as a drop shadow. */
  --chart-tint: #fdf2f8;

  /* Neutrals — paper and hairlines */
  --bg: #ffffff;
  --surface: #ffffff;
  --surface-muted: #f7f7f7;
  --border: #e6e6e6;
  --border-strong: #111111;
  --text: #111111;
  --text-body: #3d3d3d;
  --text-muted: #8c8c8c;
  --text-faint: #9a9a9a;

  /* Status — desaturated ink on a barely-tinted ground, so a table of badges
     still reads as one printed page instead of a traffic light. */
  --success-bg: #edf3ee;
  --success-fg: #2f5d43;
  --warning-bg: #f7f1e3;
  --warning-fg: #9c7c2e;
  --danger-bg: #f8eded;
  --danger-fg: #8c3a3a;
  --info-bg: #eef0f4;
  --info-fg: #3f5068;

  /* Spacing — 4px base */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;

  /* Radii — near-square; panels get 4px, controls get 2px */
  --radius-sm: 2px;
  --radius-md: 2px;
  --radius-lg: 4px;
  --radius-pill: 999px;

  /* Elevation — none. Kept as tokens so components referencing them stay valid;
     hairline borders carry all the separation in this language. */
  --shadow-xs: none;
  --shadow-sm: none;
  --shadow-md: none;

  /* Type */
  --text-xs: 0.6875rem;
  --text-sm: 0.8125rem;
  --text-base: 0.875rem;
  --text-md: 0.9375rem;
  --text-lg: 1.0625rem;
  --text-2xl: 1.75rem;
  --text-3xl: 1.875rem;

  --tracking-tight: 0.01em;
  --tracking-wide: 0.16em;

  /* Shell geometry */
  --sidebar-w: 272px;
  --topbar-h: 56px;
  --content-max: 1440px;

  --transition: 0.15s ease;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* Baseline focus ring. :focus-visible so it appears for keyboard users without
   drawing a ring around every clicked button. Individual components that set
   `outline: none` re-declare their own :focus-visible treatment. */
:focus-visible {
  outline: 2px solid var(--brand-500);
  outline-offset: 2px;
  border-radius: 2px;
}

/* Visible to screen readers only: gives an icon-only or placeholder-only
   control a real accessible name without changing the layout. */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

body {
  font-family: var(--font-sans);
  font-size: 14.5px;
  background: var(--bg);
  color: var(--text-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

::selection {
  background: rgba(17, 17, 17, 0.08);
}

/* --- Editorial type primitives -------------------------------------------- */

/* Serif display face for wordmark and page titles */
.doc-title {
  font-family: var(--font-serif);
  font-weight: 800;
  letter-spacing: 0.01em;
}

/* Panel heading: small serif caps sitting on a heavy rule, like a section head
   in a printed report */
.doc-section {
  font-family: var(--font-serif);
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.16em;
}

/* The only place gold appears in body copy: tiny label above a figure */
.eyebrow {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.22em;
  color: var(--gold);
}

/* --- Motion --------------------------------------------------------------- */

@keyframes pop-in {
  from { opacity: 0; transform: translateY(6px) scale(0.98); }
  to   { opacity: 1; transform: none; }
}

.pop-in {
  animation: pop-in 0.25s ease-out both;
}

@keyframes float-soft {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-4px); }
}

.float {
  animation: float-soft 3.2s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .pop-in,
  .float {
    animation: none;
  }
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
  /* Crops the page-header mascot where it bleeds past the content column,
     instead of letting it open a horizontal scrollbar. `clip` rather than
     `hidden`: `hidden` would turn this into a scroll container and break the
     sticky top bar and filter toolbar inside it. */
  overflow-x: clip;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  /* Centred in the column left of the sidebar, so a wide viewport doesn't
     leave all the slack on one side */
  margin: 0 auto;
  padding: var(--space-8) var(--space-8) var(--space-10);
}

/* --- Page header ---------------------------------------------------------- */

/* Two columns: the mascot spans both title rows so it sits centred against the
   whole block. Views render `<h2>` plus an optional `<p>`, so the mascot is
   injected here rather than repeated in seven templates. Purely decorative —
   the heading beside it carries the meaning. */
.page-header {
  position: relative;
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

/* Mascot rides the header on every view — it lives here rather than in seven
   templates. Taken out of flow and hung off the right edge so it can be large
   without the header reserving any height for it: the first panel still starts
   directly under the title. It bleeds past the content column and is clipped by
   the `overflow-x: clip` on `.app-main`, which is the intended crop.

   Anchored from the top so it grows downward. Anchoring from the bottom sent it
   up behind the sticky filter bar (z-index 80), which left only its feet
   showing. Growing downward runs it into the first panel instead, so it sits on
   a negative layer: negative z-index descendants paint before in-flow block
   backgrounds, which puts the opaque panels over it while the page stays behind
   it. The head reads in the header band and the body disappears under the
   panels — big, bleeding, and obscuring no figure.
   Purely decorative; the heading beside it carries the meaning. */
.page-header::after {
  content: '';
  position: absolute;
  right: -56px;
  top: -32px;
  width: 260px;
  height: 260px;
  background: url('/mascot.png') top center / contain no-repeat;
  animation: float-soft 3.2s ease-in-out infinite;
  pointer-events: none;
  z-index: -1;
}

/* Keeps the title above the mascot where the two overlap */
.page-header h2,
.page-header p {
  position: relative;
  z-index: 1;
}

.page-header h2 {
  font-family: var(--font-serif);
  font-size: 2rem;
  font-weight: 800;
  color: var(--text);
  margin-bottom: var(--space-2);
  letter-spacing: var(--tracking-tight);
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-sm);
}


/* --- Buttons -------------------------------------------------------------- */
/* For restyling buttons the app already has. This redesign adds no new buttons. */

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0.4375rem var(--space-4);
  border-radius: var(--radius-sm);
  font-size: 12.5px;
  font-weight: 600;
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  transition: background var(--transition), border-color var(--transition), color var(--transition);
  white-space: nowrap;
}

.btn:hover {
  border-color: var(--text);
  color: var(--text);
}

.btn svg {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--brand-900);
  border-color: var(--brand-900);
  color: #fff;
}

.btn-primary:hover {
  background: var(--brand-700);
  border-color: var(--brand-700);
  color: #fff;
}

.btn-secondary {
  background: var(--surface);
  color: var(--text);
  border-color: var(--border);
}

.btn-secondary:hover {
  background: var(--surface-muted);
  border-color: var(--text);
}

/* Square icon-only button — used by FilterBar's existing reset control */
.icon-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid transparent;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  transition: background var(--transition), color var(--transition), border-color var(--transition);
}

.icon-btn svg {
  width: 17px;
  height: 17px;
}

.icon-btn:hover:not(:disabled) {
  background: var(--surface-muted);
  border-color: var(--border);
  color: var(--text);
}

.icon-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

/* --- Form controls -------------------------------------------------------- */

input,
select,
textarea {
  font-family: inherit;
}

/* --- KPI cards ------------------------------------------------------------ */

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  transition: border-color var(--transition);
}

.stat-card:hover {
  border-color: var(--border-strong);
}

/* Gold eyebrow over every figure — the system's one recurring accent */
.stat-label {
  color: var(--gold);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.22em;
  margin-bottom: var(--space-3);
}

/* Figures set in the mono face with tabular digits so columns of KPIs align */
.stat-value {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
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
  padding-bottom: var(--space-3);
  /* Heavier rule than a plain divider — this is a printed section head */
  border-bottom: 1.5px solid var(--text);
}

.card-title {
  font-family: var(--font-serif);
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.16em;
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
  background: transparent;
  border-top: none;
  border-bottom: 1px solid var(--text);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: 700;
  color: var(--text-muted);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  white-space: nowrap;
}

td {
  padding: var(--space-3);
  border-top: 1px solid var(--border);
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

td.num {
  font-family: var(--font-mono);
}

/* --- Badges --------------------------------------------------------------- */

.badge {
  display: inline-block;
  padding: 0.1875rem var(--space-2);
  border: 1px solid currentColor;
  border-radius: var(--radius-sm);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
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
  background: var(--surface-muted);
  color: var(--text-muted);
}

/* --- States --------------------------------------------------------------- */

.loading {
  text-align: center;
  padding: var(--space-10);
  color: var(--text-muted);
  font-size: var(--text-sm);
  text-transform: uppercase;
  letter-spacing: 0.16em;
}

/* Static "Loading..." text reads as a stalled page on a slow connection, so
   pair it with motion that shows the fetch is still in flight. */
.loading::before {
  content: '';
  display: block;
  width: 22px;
  height: 22px;
  margin: 0 auto var(--space-4);
  border: 2px solid var(--border);
  border-top-color: var(--text);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .loading::before {
    animation-duration: 2.4s;
  }
}

.error {
  background: var(--danger-bg);
  border: 1px solid var(--danger-fg);
  color: var(--danger-fg);
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  margin: var(--space-4) 0;
  font-size: var(--text-sm);
}
</style>
