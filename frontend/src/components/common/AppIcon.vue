<template>
  <svg
    class="app-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="(d, index) in paths" :key="index" :d="d" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 18 },
})

/** Hand-written icon set — no icon font, no external package. */
const ICONS = {
  search: ['M11 4a7 7 0 1 1 0 14a7 7 0 0 1 0-14', 'M20.5 20.5 16.2 16.2'],
  bag: ['M6.5 8h11l-1 12h-9l-1-12', 'M9.2 8a2.8 2.8 0 0 1 5.6 0'],
  close: ['M6.5 6.5l11 11', 'M17.5 6.5l-11 11'],
  menu: ['M4 7h16', 'M4 12h16', 'M4 17h16'],
  chevronDown: ['M6 9.5l6 6 6-6'],
  chevronLeft: ['M15 5.5l-6.5 6.5L15 18.5'],
  chevronRight: ['M9 5.5L15.5 12 9 18.5'],
  arrowLeft: ['M19.5 12H5', 'M11 5.5L4.5 12 11 18.5'],
  arrowRight: ['M4.5 12H19', 'M13 5.5L19.5 12 13 18.5'],
  plus: ['M12 5v14', 'M5 12h14'],
  minus: ['M5 12h14'],
  check: ['M5 12.5l4.5 4.5L19 7'],
  trash: ['M4 7h16', 'M9.5 7V4.5h5V7', 'M6.5 7l1 13h9l1-13', 'M10 11v5.5', 'M14 11v5.5'],
  edit: ['M4 20h4L18.5 9.5l-4-4L4 16v4Z', 'M13.5 6.5l4 4'],
  warning: ['M12 4.5 3 20h18L12 4.5Z', 'M12 10.5v4', 'M12 17.5h.01'],
  info: ['M12 4a8 8 0 1 1 0 16a8 8 0 0 1 0-16', 'M12 11v5', 'M12 8h.01'],
  refresh: ['M19.5 12a7.5 7.5 0 1 1-2.2-5.3', 'M19.5 4.5v4.7h-4.7'],
  user: ['M12 12a3.75 3.75 0 1 0 0-7.5A3.75 3.75 0 0 0 12 12', 'M4.8 20a7.2 7.2 0 0 1 14.4 0'],
  inbox: ['M4 13.5h4.6l1.4 2.5h4l1.4-2.5H20', 'M4 13.5 6.7 5.5h10.6L20 13.5v5.5H4v-5.5Z'],
  package: ['M12 3.5 4.5 7.2v9.6L12 20.5l7.5-3.7V7.2L12 3.5Z', 'M4.5 7.2 12 11l7.5-3.8', 'M12 11v9.5'],
  database: [
    'M12 3.5c4.4 0 7.5 1.2 7.5 2.7S16.4 8.9 12 8.9 4.5 7.7 4.5 6.2 7.6 3.5 12 3.5Z',
    'M4.5 6.2v11.6c0 1.5 3.1 2.7 7.5 2.7s7.5-1.2 7.5-2.7V6.2',
    'M4.5 12c0 1.5 3.1 2.7 7.5 2.7s7.5-1.2 7.5-2.7',
  ],
  clock: ['M12 4a8 8 0 1 1 0 16a8 8 0 0 1 0-16', 'M12 8v4.4l3 1.6'],
  tag: ['M4 4.5h6.8l8.7 8.7-6.3 6.3-8.7-8.7V4.5Z', 'M8 8h.01'],
  filter: ['M4 6.5h16', 'M7 12h10', 'M10 17.5h4'],
  xCircle: ['M12 4a8 8 0 1 1 0 16a8 8 0 0 1 0-16', 'M9.5 9.5l5 5', 'M14.5 9.5l-5 5'],
  external: ['M14 5h5v5', 'M19 5l-7.5 7.5', 'M18 14v4.5A1.5 1.5 0 0 1 16.5 20h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10'],
  chart: ['M4 19.5h16', 'M7 16V10', 'M12 16V5.5', 'M17 16v-4'],
}

const paths = computed(() => ICONS[props.name] || ICONS.info)
</script>

<style scoped>
.app-icon {
  flex: none;
  display: block;
}
</style>
