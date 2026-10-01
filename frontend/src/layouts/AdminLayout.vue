<template>
  <div class="admin" :class="{ 'admin--nav-open': navOpen }">
    <aside class="sidebar" aria-label="Admin navigation">
      <div class="sidebar__brand">
        <RouterLink to="/" class="brand">
          <span class="brand__mark" aria-hidden="true">M</span>
          <span class="brand__name">Meridian</span>
        </RouterLink>
        <button
          type="button"
          class="sidebar__close only-mobile"
          aria-label="Close navigation"
          @click="navOpen = false"
        >
          <AppIcon name="close" :size="18" />
        </button>
      </div>

      <p class="sidebar__section">Admin</p>

      <nav class="sidebar__nav">
        <RouterLink
          :to="{ name: 'admin-search' }"
          class="sidebar__link"
          active-class="is-active"
          @click="navOpen = false"
        >
          <AppIcon name="chart" :size="17" />
          <span>Search dashboard</span>
        </RouterLink>
        <RouterLink
          :to="{ name: 'catalog-admin' }"
          class="sidebar__link"
          active-class="is-active"
          @click="navOpen = false"
        >
          <AppIcon name="package" :size="17" />
          <span>Catalog admin</span>
        </RouterLink>
      </nav>

      <div class="sidebar__foot">
        <p class="sidebar__section">Data sources</p>
        <p class="text-xs muted sidebar__sources">
          <AppIcon name="database" :size="14" />
          MongoDB · PostgreSQL · Elasticsearch
        </p>
        <RouterLink to="/" class="text-sm sidebar__store-link">
          <AppIcon name="arrowLeft" :size="14" />
          View storefront
        </RouterLink>
        <div class="sidebar__user" v-if="authStore.isAuthenticated">
          <div class="sidebar__user-info">
            <span class="sidebar__user-name">{{ authStore.userName }}</span>
            <span class="sidebar__user-role">{{ authStore.user?.role }}</span>
          </div>
          <BaseButton
            variant="ghost"
            size="sm"
            @click="logout"
            class="sidebar__logout"
          >
            <AppIcon name="logout" :size="14" />
            <span>Logout</span>
          </BaseButton>
        </div>
      </div>
    </aside>

    <Transition name="fade">
      <div v-if="navOpen" class="sidebar-overlay" @click="navOpen = false" />
    </Transition>

    <div class="admin__main">
      <header class="admin__topbar">
        <button
          type="button"
          class="admin__hamburger only-mobile"
          aria-label="Open navigation"
          @click="navOpen = true"
        >
          <AppIcon name="menu" :size="18" />
        </button>
        <h1 class="admin__title">{{ pageTitle }}</h1>
      </header>

      <main class="admin__content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '../components/common/AppIcon.vue'
import BaseButton from '../components/common/BaseButton.vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const navOpen = ref(false)

const pageTitle = computed(() => route.meta?.title || 'Admin')

watch(
  () => route.fullPath,
  () => {
    navOpen.value = false
  },
)

async function logout() {
  await authStore.logout()
  navOpen.value = false
}
</script>

<style scoped>
.admin {
  min-height: 100vh;
}

/* ---------------- sidebar ---------------- */

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-w);
  z-index: 50;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
}

.sidebar__brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text);
  font-weight: var(--fw-semibold);
  font-size: var(--text-md);
}

.brand:hover {
  text-decoration: none;
}

.brand__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: var(--on-accent);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
}

.sidebar__close,
.admin__hamburger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
}

.sidebar__section {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-faint);
  padding: var(--space-3) var(--space-2) var(--space-1);
}

.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 9px 10px;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: var(--text-base);
  transition: background-color var(--transition), color var(--transition);
}

.sidebar__link:hover {
  background: var(--surface-2);
  color: var(--text);
  text-decoration: none.
}

.sidebar__link.is-active {
  background: var(--accent-soft);
  color: var(--accent-text);
  font-weight: var(--fw-medium);
}

.sidebar__foot {
  margin-top: auto;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar__sources,
.sidebar__store-link {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: 0 var(--space-2) var(--space-1);
}

.sidebar__store-link {
  color: var(--text-muted);
}

.sidebar__user {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.sidebar__user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar__user-name {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--text);
}

.sidebar__user-role {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: uppercase;
}

.sidebar__logout {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  width: fit-content;
}

.sidebar-overlay {
  display: none;
}

/* ---------------- main ---------------- */

.admin__main {
  margin-left: var(--sidebar-w);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.admin__topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--surface);
  border-bottom: 1px solid var(--border).
}

.admin__title {
  font-size: var(--text-lg);
}

.admin__content {
  flex: 1 1 auto;
  width: 100%;
  max-width: var(--admin-max);
  margin: 0 auto;
  padding: var(--space-5);
}

/* ---------------- responsive ---------------- */

@media (max-width: 900px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform var(--transition);
    box-shadow: var(--shadow-2);
  }

  .admin--nav-open .sidebar {
    transform: translateX(0);
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 45;
    background: rgba(18, 22, 29, 0.45);
  }

  .admin__main {
    margin-left: 0;
  }

  .admin__hamburger {
    display: inline-flex;
  }

  .admin__content {
    padding: var(--space-4);
  }

  .fade-enter-active,
  .fade-leave-active {
    transition: opacity var(--transition);
  }

  .fade-enter-from,
  .fade-leave-to {
    opacity: 0;
  }
}
</style>