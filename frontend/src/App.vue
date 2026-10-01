<template>
  <router-view />
  <ToastHost />
</template>

<script setup>
import ToastHost from './components/common/ToastHost.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
authStore.init()
</script>