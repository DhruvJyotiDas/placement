<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, download, notify, formatDate, statusColor } from '../api.js'

const route = useRoute()
const router = useRouter()
const applicationId = route.params.id

const application = ref(null)
const status = ref('')
const interviewMode = ref('')
const interviewDate = ref('')
const remark = ref('')
const loading = ref(true)
const busy = ref(false)

// The wireframe's dropdown, plus the two terminal outcomes.
const STATUSES = ['applied', 'shortlisted', 'waiting', 'selected', 'rejected']
const MODES = ['In-person', 'Online', 'Telephonic']

async function load() {
  try {
    const data = await api(`/api/company/applications/${applicationId}`)
    application.value = data
    status.value = data.status
    interviewMode.value = data.interview_mode
    interviewDate.value = data.interview_date ? data.interview_date.slice(0, 16) : ''
    remark.value = data.remark
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    loading.value = false
  }
}

async function save() {
  busy.value = true
  try {
    const data = await api(`/api/company/applications/${applicationId}`, {
      method: 'PUT',
      body: {
        status: status.value,
        interview_mode: interviewMode.value,
        interview_date: interviewDate.value || null,
        remark: remark.value,
      },
    })
    notify(data.message)
    router.push(`/company/drives/${application.value.drive_id}/applications`)
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    busy.value = false
  }
}

async function viewResume() {
  try {
    await download(
      `/api/company/resume/${applicationId}`,
      `${application.value.roll_number}_resume.pdf`,
    )
  } catch {
    notify('This student has not uploaded a resume', 'warning')
  }
}

onMounted(load)
</script>

<template>
  <div v-if="loading" class="text-center text-muted py-5">Loading…</div>

  <div v-else-if="application" class="row justify-content-center">
    <div class="col-lg-7">
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><router-link to="/company">Dashboard</router-link></li>
          <li class="breadcrumb-item">
            <router-link :to="`/company/drives/${application.drive_id}/applications`">
              {{ application.drive_name }}
            </router-link>
          </li>
          <li class="breadcrumb-item active" aria-current="page">{{ application.student_name }}</li>
        </ol>
      </nav>

      <div class="card shadow-sm">
        <div class="card-header fw-semibold">Student Application</div>

        <div class="card-body p-4">
          <dl class="row">
            <dt class="col-sm-4">Student Name</dt>
            <dd class="col-sm-8">{{ application.student_name }}</dd>

            <dt class="col-sm-4">Roll Number</dt>
            <dd class="col-sm-8">{{ application.roll_number }}</dd>

            <dt class="col-sm-4">Department</dt>
            <dd class="col-sm-8">{{ application.branch }}</dd>

            <dt class="col-sm-4">CGPA</dt>
            <dd class="col-sm-8">{{ application.cgpa }}</dd>

            <dt class="col-sm-4">Drive</dt>
            <dd class="col-sm-8">{{ application.drive_name }}</dd>

            <dt class="col-sm-4">Job Title</dt>
            <dd class="col-sm-8">{{ application.job_title }}</dd>

            <dt class="col-sm-4">Applied On</dt>
            <dd class="col-sm-8">{{ formatDate(application.application_date) }}</dd>

            <dt class="col-sm-4">Current Status</dt>
            <dd class="col-sm-8">
              <span :class="`badge bg-${statusColor(application.status)}`">
                {{ application.status }}
              </span>
            </dd>
          </dl>

          <hr />

          <div class="row g-3 align-items-end">
            <div class="col-sm-4">
              <label class="form-label small">Set Status</label>
              <select v-model="status" class="form-select">
                <option v-for="s in STATUSES" :key="s" :value="s">
                  {{ s.charAt(0).toUpperCase() + s.slice(1) }}
                </option>
              </select>
            </div>

            <div class="col-sm-4">
              <label class="form-label small">Interview Mode</label>
              <select v-model="interviewMode" class="form-select">
                <option v-for="m in MODES" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>

            <div class="col-sm-4">
              <label class="form-label small">Interview Date &amp; Time</label>
              <input v-model="interviewDate" type="datetime-local" class="form-control" />
            </div>

            <div class="col-sm-4">
              <button class="btn btn-outline-secondary w-100" @click="viewResume">
                View resume
              </button>
            </div>

            <div class="col-12">
              <label class="form-label small">Remark</label>
              <input v-model="remark" class="form-control" placeholder="None" />
            </div>
          </div>

          <div class="d-flex justify-content-end gap-2 mt-4">
            <button class="btn btn-outline-secondary" @click="router.back()">Back</button>
            <button class="btn btn-success" :disabled="busy" @click="save">
              {{ busy ? 'Saving…' : 'Save' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
