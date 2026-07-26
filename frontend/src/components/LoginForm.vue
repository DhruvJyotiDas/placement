<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, auth, notify } from '../api.js'

const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const data = await api('/api/login', {
      method: 'POST',
      body: { email: email.value, password: password.value },
    })
    auth.login(data)
    notify(`Welcome back, ${data.email}`)
    router.push(`/${data.role}`)
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="auth-bg">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-5 col-lg-4">
          <div class="text-center mb-4">
            <h2 class="fw-bold mb-1">Welcome to Placement Portal</h2>
            <p class="text-muted">Version 2</p>
          </div>

          <div class="card shadow-sm">
            <div class="card-body p-4">
              <h4 class="card-title mb-4">Login Form</h4>

              <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>

              <form @submit.prevent="submit">
                <div class="form-floating mb-3">
                  <input
                    v-model="email"
                    type="email"
                    class="form-control"
                    id="loginEmail"
                    placeholder="name@example.com"
                    required
                  />
                  <label for="loginEmail">Username (email)</label>
                </div>

                <div class="form-floating mb-4">
                  <input
                    v-model="password"
                    type="password"
                    class="form-control"
                    id="loginPassword"
                    placeholder="Password"
                    required
                  />
                  <label for="loginPassword">Password</label>
                </div>

                <button class="btn btn-primary w-100" :disabled="busy">
                  {{ busy ? 'Logging in…' : 'Login' }}
                </button>
              </form>

              <p class="text-center text-muted mt-3 mb-0 small">
                Do not have an account?
                <router-link to="/register">Register</router-link>
              </p>
            </div>
          </div>

          <p class="text-center text-muted small mt-3">
            Admin: <code>admin@ppa.com</code> / <code>admin123</code>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
