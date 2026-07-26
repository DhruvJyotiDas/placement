<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, notify } from '../api.js'

const router = useRouter()

// Students and companies self-register. Admin never can.
const role = ref('student')
const error = ref('')
const busy = ref(false)

const form = reactive({
  email: '',
  password: '',
  // student fields
  name: '',
  roll_number: '',
  branch: '',
  cgpa: '',
  year: 4,
  // company fields
  company_name: '',
  hr_contact: '',
  website: '',
  description: '',
})

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const data = await api('/api/register', {
      method: 'POST',
      body: { ...form, role: role.value },
    })
    notify(data.message)
    router.push('/login')
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="auth-bg py-5">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-6 col-lg-5">
          <div class="text-center mb-4">
            <h2 class="fw-bold mb-1">Welcome to Placement Portal</h2>
            <p class="text-muted">Version 2</p>
          </div>

          <div class="card shadow-sm">
        <div class="card-body p-4">
          <h4 class="card-title mb-4">Register Form</h4>

          <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>

          <div class="btn-group w-100 mb-4" role="group">
            <button
              type="button"
              class="btn rounded-pill me-2"
              :class="role === 'student' ? 'btn-primary' : 'btn-outline-primary'"
              @click="role = 'student'"
            >
              I am a Student
            </button>
            <button
              type="button"
              class="btn rounded-pill"
              :class="role === 'company' ? 'btn-primary' : 'btn-outline-primary'"
              @click="role = 'company'"
            >
              I am a Company
            </button>
          </div>

          <form @submit.prevent="submit">
            <div class="form-floating mb-3">
              <input
                v-model="form.email"
                type="email"
                class="form-control"
                id="regEmail"
                placeholder="name@example.com"
                required
              />
              <label for="regEmail">Username (email)</label>
            </div>

            <div class="form-floating mb-3">
              <input
                v-model="form.password"
                type="password"
                class="form-control"
                id="regPassword"
                placeholder="Password"
                required
              />
              <label for="regPassword">Password</label>
            </div>

            <!-- Student-specific -->
            <template v-if="role === 'student'">
              <div class="mb-3">
                <label class="form-label">Full Name</label>
                <input v-model="form.name" class="form-control" required />
              </div>
              <div class="row">
                <div class="col mb-3">
                  <label class="form-label">Roll Number</label>
                  <input v-model="form.roll_number" class="form-control" required />
                </div>
                <div class="col mb-3">
                  <label class="form-label">Branch</label>
                  <input
                    v-model="form.branch"
                    class="form-control"
                    placeholder="Computer Science"
                    required
                  />
                </div>
              </div>
              <div class="row">
                <div class="col mb-3">
                  <label class="form-label">CGPA</label>
                  <input
                    v-model="form.cgpa"
                    type="number"
                    step="0.01"
                    min="0"
                    max="10"
                    class="form-control"
                    required
                  />
                </div>
                <div class="col mb-3">
                  <label class="form-label">Year</label>
                  <select v-model.number="form.year" class="form-select">
                    <option :value="1">1</option>
                    <option :value="2">2</option>
                    <option :value="3">3</option>
                    <option :value="4">4</option>
                  </select>
                </div>
              </div>
            </template>

            <!-- Company-specific -->
            <template v-else>
              <div class="mb-3">
                <label class="form-label">Company Name</label>
                <input v-model="form.company_name" class="form-control" required />
              </div>
              <div class="mb-3">
                <label class="form-label">HR Contact</label>
                <input v-model="form.hr_contact" class="form-control" />
              </div>
              <div class="mb-3">
                <label class="form-label">Website</label>
                <input v-model="form.website" class="form-control" placeholder="https://…" />
              </div>
              <div class="mb-3">
                <label class="form-label">Overview</label>
                <textarea v-model="form.description" class="form-control" rows="3"></textarea>
              </div>
              <div class="alert alert-info py-2 small">
                Your company must be approved by the admin before you can create drives.
              </div>
            </template>

            <button class="btn btn-primary w-100" :disabled="busy">
              {{ busy ? 'Registering…' : 'Register' }}
            </button>
          </form>

          <p class="text-center text-muted mt-3 mb-0 small">
            Already have an account?
            <router-link to="/login">Login</router-link>
          </p>
          </div>
        </div>
        </div>
      </div>
    </div>
  </div>
</template>
