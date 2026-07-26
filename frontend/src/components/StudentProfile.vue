<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api, download, notify } from '../api.js'

const form = reactive({ name: '', branch: '', cgpa: 0, year: 4 })
const rollNumber = ref('')
const resumePath = ref('')

const loading = ref(true)
const saving = ref(false)
const uploading = ref(false)
const fileInput = ref(null)

async function load() {
  try {
    const data = await api('/api/student/profile')
    Object.assign(form, {
      name: data.name,
      branch: data.branch,
      cgpa: data.cgpa,
      year: data.year,
    })
    rollNumber.value = data.roll_number
    resumePath.value = data.resume_path
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const data = await api('/api/student/profile', { method: 'PUT', body: form })
    notify(data.message)
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    saving.value = false
  }
}

async function uploadResume() {
  const file = fileInput.value?.files?.[0]
  if (!file) return notify('Choose a file first', 'warning')

  const body = new FormData()
  body.append('resume', file)

  uploading.value = true
  try {
    const data = await api('/api/student/resume', { method: 'POST', body, isForm: true })
    resumePath.value = data.resume_path
    notify(data.message)
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    uploading.value = false
  }
}

async function viewResume() {
  await download('/api/student/resume', resumePath.value)
}

// A quick, honest nudge — not enforced, just encouraged.
const completeness = computed(() => {
  const checks = [!!form.name, !!form.branch, form.cgpa > 0, !!resumePath.value]
  return Math.round((100 * checks.filter(Boolean).length) / checks.length)
})

onMounted(load)
</script>

<template>
  <div v-if="loading" class="text-center text-muted py-5">Loading…</div>

  <div v-else class="row justify-content-center">
    <div class="col-lg-6">
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><router-link to="/student">Dashboard</router-link></li>
          <li class="breadcrumb-item active" aria-current="page">Edit Profile</li>
        </ol>
      </nav>

      <div class="card shadow-sm mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span class="fw-semibold">Edit Profile</span>
          <span class="small text-muted">{{ completeness }}% complete</span>
        </div>
        <div class="progress rounded-0" style="height: 4px">
          <div
            class="progress-bar"
            :class="completeness === 100 ? 'bg-success' : 'bg-info'"
            :style="`width: ${completeness}%`"
          ></div>
        </div>
        <div class="card-body p-4">
          <form @submit.prevent="save">
            <div class="mb-3">
              <label class="form-label">Roll Number</label>
              <input :value="rollNumber" class="form-control" disabled />
              <div class="form-text">Your roll number cannot be changed.</div>
            </div>

            <div class="mb-3">
              <label class="form-label">Full Name</label>
              <input v-model="form.name" class="form-control" required />
            </div>

            <div class="mb-3">
              <label class="form-label">Branch / Department</label>
              <input v-model="form.branch" class="form-control" required />
            </div>

            <div class="row">
              <div class="col mb-3">
                <label class="form-label">CGPA</label>
                <input
                  v-model.number="form.cgpa"
                  type="number"
                  step="0.01"
                  min="0"
                  max="10"
                  class="form-control"
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

            <button class="btn btn-primary w-100" :disabled="saving">
              {{ saving ? 'Saving…' : 'Save Profile' }}
            </button>
          </form>
        </div>
      </div>

      <div class="card shadow-sm">
        <div class="card-header fw-semibold">Resume</div>
        <div class="card-body p-4">
          <div v-if="resumePath" class="alert alert-success py-2 small d-flex justify-content-between align-items-center">
            <span>Uploaded: <b>{{ resumePath }}</b></span>
            <button class="btn btn-sm btn-outline-success" @click="viewResume">View</button>
          </div>
          <div v-else class="alert alert-warning py-2 small">No resume uploaded yet.</div>

          <div class="input-group">
            <input ref="fileInput" type="file" class="form-control" accept=".pdf,.doc,.docx" />
            <button class="btn btn-outline-primary" :disabled="uploading" @click="uploadResume">
              {{ uploading ? 'Uploading…' : 'Upload' }}
            </button>
          </div>
          <div class="form-text">PDF, DOC or DOCX.</div>
        </div>
      </div>
    </div>
  </div>
</template>
