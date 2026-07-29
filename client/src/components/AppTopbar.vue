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

// Exists to give ProfileMenu a home now that the top nav bar is gone.
// Events are re-emitted so App.vue's existing handlers stay unchanged.
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
  height: var(--topbar-h);
  padding: 0 var(--space-8);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.topbar-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
</style>
