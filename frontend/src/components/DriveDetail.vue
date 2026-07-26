<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, notify, formatDate } from '../api.js'

const route = useRoute()
const router = useRouter()

const drive = ref(null)
const loading = ref(true)
const busy = ref(false)

async function load() {
  try {
    drive.value = await api(`/api/student/drives/${route.params.id}`)
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    loading.value = false
  }
}

async function apply() {
  busy.value = true
  try {
    const data = await api(`/api/student/drives/${drive.value.id}/apply`, { method: 'POST' })
    notify(data.message)
    router.push('/student')
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-if="loading" class="text-center text-muted py-5">Loading…</div>

  <div v-else-if="drive" class="row justify-content-center">
    <div class="col-lg-7">
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><router-link to="/student">Dashboard</router-link></li>
          <li class="breadcrumb-item">
            <router-link :to="`/student/companies/${drive.company_id}`">{{ drive.company_name }}</router-link>
          </li>
          <li class="breadcrumb-item active" aria-current="page">{{ drive.drive_name }}</li>
        </ol>
      </nav>

      <div class="card shadow-sm">
        <div class="card-body p-4">
          <div class="d-flex justify-content-between align-items-start mb-4">
            <div>
              <h4 class="mb-1">{{ drive.drive_name }}</h4>
              <div class="text-muted">{{ drive.job_title }}</div>
            </div>
            <router-link
              class="text-decoration-none text-end"
              :to="`/student/companies/${drive.company_id}`"
            >
              <div class="fw-semibold">{{ drive.company_name }}</div>
              <div class="small">View company</div>
            </router-link>
          </div>

          <h6 class="text-muted">Job Description</h6>
          <p>{{ drive.job_description || 'No description provided.' }}</p>

          <hr />

          <dl class="row mb-0">
            <dt class="col-sm-4">Salary</dt>
            <dd class="col-sm-8">₹{{ drive.salary.toLocaleString('en-IN') }}</dd>

            <dt class="col-sm-4">Location</dt>
            <dd class="col-sm-8">{{ drive.location || '—' }}</dd>

            <dt class="col-sm-4">Eligible Branches</dt>
            <dd class="col-sm-8">{{ drive.eligible_branches }}</dd>

            <dt class="col-sm-4">Minimum CGPA</dt>
            <dd class="col-sm-8">{{ drive.min_cgpa }}</dd>

            <dt class="col-sm-4">Eligible Year</dt>
            <dd class="col-sm-8">{{ drive.eligible_year }}</dd>

            <dt class="col-sm-4">Application Deadline</dt>
            <dd class="col-sm-8">{{ formatDate(drive.deadline) }}</dd>

            <dt class="col-sm-4">Applicants so far</dt>
            <dd class="col-sm-8">{{ drive.applicant_count }}</dd>
          </dl>

          <div v-if="!drive.eligible" class="alert alert-danger mt-4 py-2 small">
            You are not eligible for this drive — {{ drive.ineligible_reason }}
          </div>

          <div class="d-flex justify-content-end gap-2 mt-4">
            <button class="btn btn-outline-secondary" @click="router.back()">Go Back</button>

            <button v-if="drive.already_applied" class="btn btn-secondary" disabled>
              Already Applied
            </button>
            <button
              v-else
              class="btn btn-primary"
              :disabled="!drive.eligible || busy"
              @click="apply"
            >
              {{ busy ? 'Applying…' : 'Apply' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
