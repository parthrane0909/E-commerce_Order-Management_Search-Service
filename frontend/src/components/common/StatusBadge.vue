<template>
  <AppBadge :tone="tone" :size="size" dot>{{ label }}</AppBadge>
</template>

<script setup>
import { computed } from 'vue'
import AppBadge from './AppBadge.vue'
import { statusLabel, statusTone } from '../../utils/status'

const props = defineProps({
  status: { type: String, default: '' },
  size: { type: String, default: 'md' },
})

const label = computed(() => statusLabel(props.status))
const tone = computed(() => statusTone(props.status))
</script>
