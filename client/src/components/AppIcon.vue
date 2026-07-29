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
    <path v-for="d in paths" :key="d" :d="d" />
  </svg>
</template>

<script>
import { computed } from 'vue'

// Each entry is a list of path `d` strings drawn with a shared stroke style.
// Keeping icons here avoids adding an icon library dependency.
const ICONS = {
  overview: ['M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z'],
  inventory: ['M3 5h18v14H3z', 'M3 9h18', 'M9 13h6'],
  orders: [
    'M6 6h15l-1.5 8h-12z',
    'M6 6L5 3H2',
    'M9 20a1 1 0 100-2 1 1 0 000 2z',
    'M18 20a1 1 0 100-2 1 1 0 000 2z'
  ],
  finance: ['M2 6h20v12H2z', 'M2 10h20', 'M6 15h4'],
  demand: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'],
  restocking: [
    'M3 6h11v10H3z',
    'M14 9h4l3 3v4h-7z',
    'M7.5 19a1.5 1.5 0 100-3 1.5 1.5 0 000 3z',
    'M17.5 19a1.5 1.5 0 100-3 1.5 1.5 0 000 3z'
  ],
  reports: ['M4 20V10', 'M10 20V4', 'M16 20v-7', 'M22 20H2']
}

export default {
  name: 'AppIcon',
  props: {
    name: { type: String, required: true },
    size: { type: [Number, String], default: 20 }
  },
  setup(props) {
    // Unknown names render nothing rather than throwing, so a typo can't blank a page.
    const paths = computed(() => ICONS[props.name] || [])
    return { paths }
  }
}
</script>
