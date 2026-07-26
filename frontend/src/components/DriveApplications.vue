<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api, notify, formatDate, statusColor, initials, avatarColor } from '../api.js'

const route = useRoute()
const driveId = route.params.id

const drive = ref({})
const applications = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const [d, a] = await Promise.all([
      api(`/api/company/drives/${driveId}`),
      api(`/api/company/drives/${driveId}/applications`),
    ])
    drive.value = d
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
    <div class="col-lg-9">
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><router-link to="/company">Dashboard</router-link></li>
          <li class="breadcrumb-item active" aria-current="page">{{ drive.drive_name }}</li>
        </ol>
      </nav>

      <div class="card shadow-sm">
        <div class="card-header d-flex justify-content-between align-items-center">
          <div>
            <div class="fw-semibold">Update Applications for the Drive</div>
            <div class="text-muted small">
              {{ drive.drive_name }} · Job Title: {{ drive.job_title }}
            </div>
          </div>
          <span :class="`badge bg-${statusColor(drive.status)}`">{{ drive.status }}</span>
        </div>

        <div class="card-body">
          <h6 class="text-muted mb-3">
            Received Applications
            <span class="badge bg-secondary">{{ applications.length }}</span>
          </h6>

          <div v-if="!applications.length" class="text-muted small">
            No students have applied to this drive yet.
          </div>

          <div class="table-responsive" style="max-height: 460px; overflow-y: auto">
            <table v-if="applications.length" class="table align-middle">
              <thead class="table-light">
                <tr>
                  <th>Student</th>
                  <th>Branch</th>
                  <th>CGPA</th>
                  <th>Applied On</th>
                  <th>Status</th>
                  <th class="text-end">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in applications" :key="a.id">
                  <td>
                    <div class="d-flex align-items-center gap-2">
                      <div
                        class="avatar-circle"
                        style="width: 30px; height: 30px; font-size: 0.7rem"
                        :style="`background:${avatarColor(a.student_name)}`"
                      >
                        {{ initials(a.student_name) }}
                      </div>
                      <div>
                        <div class="fw-semibold">{{ a.student_name }}</div>
                        <div class="text-muted small">{{ a.roll_number }}</div>
                      </div>
                    </div>
                  </td>
                  <td>{{ a.branch }}</td>
                  <td>{{ a.cgpa }}</td>
                  <td>{{ formatDate(a.application_date) }}</td>
                  <td>
                    <span :class="`badge bg-${statusColor(a.status)}`">{{ a.status }}</span>
                  </td>
                  <td class="text-end">
                    <router-link
                      class="btn btn-sm btn-outline-primary"
                      :to="`/company/applications/${a.id}`"
                    >
                      Review application
                    </router-link>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="d-flex justify-content-end mt-3">
            <router-link class="btn btn-outline-secondary" to="/company">Back</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
