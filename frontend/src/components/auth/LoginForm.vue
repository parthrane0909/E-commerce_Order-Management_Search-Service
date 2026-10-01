<template>
  <div class="login-form">
    <form @submit.prevent="submit" class="login-form__inner">
      <h2 class="login-form__title">Sign in to Meridian</h2>

      <div v-if="error" class="login-form__error" role="alert">
        {{ error }}
      </div>

      <FormField label="Email" :error="errors.email">
        <BaseInput
          v-model="form.email"
          type="email"
          autocomplete="email"
          placeholder="you@example.com"
          @blur="validateEmail"
        />
      </FormField>

      <FormField label="Password" :error="errors.password">
        <BaseInput
          v-model="form.password"
          type="password"
          autocomplete="current-password"
          placeholder="••••••••"
          @blur="validatePassword"
        />
      </FormField>

      <BaseButton type="submit" :loading="loading" class="login-form__submit">
        Sign in
      </BaseButton>

      <p class="login-form__demo">
        Demo accounts: john.doe@example.com / john, admin@example.com / admin
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import BaseInput from '../common/BaseInput.vue'
import BaseButton from '../common/BaseButton.vue'
import FormField from '../common/FormField.vue'

const props = defineProps({
  redirect: { type: String, default: '/' },
})

const emit = defineEmits(['success'])

const authStore = useAuthStore()

const form = ref({
  email: '',
  password: '',
})

const errors = ref({
  email: '',
  password: '',
})

const loading = computed(() => authStore.loading)

function validateEmail() {
  errors.value.email = ''
  if (!form.value.email) {
    errors.value.email = 'Email is required'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.email)) {
    errors.value.email = 'Enter a valid email address'
  }
}

function validatePassword() {
  errors.value.password = ''
  if (!form.value.password) {
    errors.value.password = 'Password is required'
  }
}

async function submit() {
  validateEmail()
  validatePassword()
  if (errors.value.email || errors.value.password) return

  try {
    await authStore.login(form.value.email, form.value.password)
    emit('success')
  } catch {
    // Error is set in the store
  }
}
</script>

<style scoped>
.login-form {
  max-width: 360px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-5);
}

.login-form__inner {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.login-form__title {
  font-size: var(--text-xl);
  font-weight: var(--fw-semibold);
  text-align: center;
  margin: 0 0 var(--space-2);
}

.login-form__error {
  padding: var(--space-3);
  background: var(--danger-soft);
  border: 1px solid var(--danger);
  border-radius: var(--radius-sm);
  color: var(--danger-text);
  font-size: var(--text-sm);
}

.login-form__submit {
  margin-top: var(--space-2);
}

.login-form__demo {
  margin: var(--space-4) 0 0;
  padding: var(--space-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-align: center;
  line-height: 1.5;
}

@media (max-width: 480px) {
  .login-form {
    padding: var(--space-4);
  }
}
</style>