<script setup>
import { onMounted, ref } from 'vue'
import { api, notify, formatDate, statusColor } from '../api.js'

const profile = ref({})
const applications = ref([])
const loading = ref(true)

async function load() {
  try {
    const [p, a] = await Promise.all([
      api('/api/student/profile'),
      api('/api/student/applications'),
    ])
    profile.value = p
    applications.value = a
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-if="loading" class="text-center text-muted py-5">Loading…</div>

  <div v-else class="row justify-content-center">
    <div class="col-lg-10">
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><router-link to="/student">Dashboard</router-link></li>
          <li class="breadcrumb-item active" aria-current="page">Application History</li>
        </ol>
      </nav>

      <div class="card shadow-sm">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span class="fw-semibold">Student Application History</span>
          <router-link class="btn btn-sm btn-outline-secondary" to="/student">Back</router-link>
        </div>

        <div class="card-body">
          <dl class="row small mb-4">
            <dt class="col-sm-2">Student Name</dt>
            <dd class="col-sm-4">{{ profile.name }}</dd>

            <dt class="col-sm-2">Department</dt>
            <dd class="col-sm-4">{{ profile.branch }}</dd>

            <dt class="col-sm-2">Roll Number</dt>
            <dd class="col-sm-4">{{ profile.roll_number }}</dd>

            <dt class="col-sm-2">CGPA</dt>
            <dd class="col-sm-4">{{ profile.cgpa }}</dd>
          </dl>

          <div class="table-responsive">
            <table class="table align-middle">
              <thead class="table-light">
                <tr>
                  <th>Sr No.</th>
                  <th>Company</th>
                  <th>Drive</th>
                  <th>Job Title</th>
                  <th>Interview</th>
                  <th>Applied On</th>
                  <th>Result</th>
                  <th>Remark</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!applications.length">
                  <td colspan="8" class="text-muted small">
                    You have not applied to any drives yet.
                  </td>
                </tr>
                <tr v-for="(a, i) in applications" :key="a.id">
                  <td>{{ i + 1 }}</td>
                  <td>{{ a.company_name }}</td>
                  <td>{{ a.drive_name }}</td>
                  <td>{{ a.job_title }}</td>
                  <td>{{ a.interview_mode }}</td>
                  <td>{{ formatDate(a.application_date) }}</td>
                  <td>
                    <span :class="`badge bg-${statusColor(a.status)}`">{{ a.status }}</span>
                  </td>
                  <td class="text-muted small">{{ a.remark }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
