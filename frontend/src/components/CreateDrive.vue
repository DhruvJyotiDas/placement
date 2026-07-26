<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, notify } from '../api.js'

const router = useRouter()

const error = ref('')
const busy = ref(false)

const form = reactive({
  drive_name: '',
  job_title: '',
  job_description: '',
  eligible_branches: 'All',
  min_cgpa: 0,
  eligible_year: 4,
  salary: 0,
  location: '',
  skills_required: '',
  experience_required: '',
  benefits: '',
  deadline: '',
})

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const data = await api('/api/company/drives', { method: 'POST', body: form })
    notify(data.message)
    router.push('/company')
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="row justify-content-center">
    <div class="col-lg-7">
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><router-link to="/company">Dashboard</router-link></li>
          <li class="breadcrumb-item active" aria-current="page">Create Drive</li>
        </ol>
      </nav>

      <div class="card shadow-sm">
        <div class="card-header fw-semibold">Create a Drive</div>
        <div class="card-body p-4">
          <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>

          <form @submit.prevent="submit">
            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Drive Name</label>
              <div class="col-sm-8">
                <input v-model="form.drive_name" class="form-control" required />
              </div>
            </div>

            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Job Title</label>
              <div class="col-sm-8">
                <input
                  v-model="form.job_title"
                  class="form-control"
                  placeholder="Senior Software Developer"
                  required
                />
              </div>
            </div>

            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Job Description</label>
              <div class="col-sm-8">
                <textarea v-model="form.job_description" class="form-control" rows="4"></textarea>
              </div>
            </div>

            <!-- Eligibility criteria: branch, CGPA, year -->
            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Eligible Branches</label>
              <div class="col-sm-8">
                <input
                  v-model="form.eligible_branches"
                  class="form-control"
                  placeholder="All, or: Computer Science, Electronics"
                />
                <div class="form-text">Comma-separated, or "All" for every branch.</div>
              </div>
            </div>

            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Minimum CGPA</label>
              <div class="col-sm-8">
                <input
                  v-model.number="form.min_cgpa"
                  type="number"
                  step="0.1"
                  min="0"
                  max="10"
                  class="form-control"
                />
              </div>
            </div>

            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Eligible Year</label>
              <div class="col-sm-8">
                <select v-model.number="form.eligible_year" class="form-select">
                  <option :value="1">1</option>
                  <option :value="2">2</option>
                  <option :value="3">3</option>
                  <option :value="4">4</option>
                </select>
              </div>
            </div>

            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Salary (per annum)</label>
              <div class="col-sm-8">
                <input v-model.number="form.salary" type="number" min="0" class="form-control" />
              </div>
            </div>

            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Location</label>
              <div class="col-sm-8">
                <input v-model="form.location" class="form-control" placeholder="Chennai" />
              </div>
            </div>

            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Skills Required</label>
              <div class="col-sm-8">
                <input
                  v-model="form.skills_required"
                  class="form-control"
                  placeholder="Python, SQL, React"
                />
                <div class="form-text">Comma-separated.</div>
              </div>
            </div>

            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Experience Required</label>
              <div class="col-sm-8">
                <input
                  v-model="form.experience_required"
                  class="form-control"
                  placeholder="Freshers, or: 1-2 years"
                />
              </div>
            </div>

            <div class="row mb-3">
              <label class="col-sm-4 col-form-label text-sm-end">Benefits</label>
              <div class="col-sm-8">
                <input
                  v-model="form.benefits"
                  class="form-control"
                  placeholder="Health insurance, relocation support"
                />
              </div>
            </div>

            <div class="row mb-4">
              <label class="col-sm-4 col-form-label text-sm-end">Application Deadline</label>
              <div class="col-sm-8">
                <input
                  v-model="form.deadline"
                  type="datetime-local"
                  class="form-control"
                  required
                />
              </div>
            </div>

            <div class="d-flex justify-content-end gap-2">
              <router-link class="btn btn-outline-secondary" to="/company">Go Back</router-link>
              <button class="btn btn-success" :disabled="busy">
                {{ busy ? 'Saving…' : 'Save' }}
              </button>
            </div>
          </form>

          <div class="alert alert-info py-2 small mt-4 mb-0">
            The drive will be visible to students only after the admin approves it.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
