<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { api, download, notify, formatDate, statusColor } from '../api.js'

const profile = ref({})
const drives = ref([])
const applications = ref([])

const search = ref('')
const eligibleOnly = ref(false)
const loading = ref(true)

// Async CSV export state
const exporting = ref(false)
const exportFile = ref('')
let poller = null

const appliedDrives = computed(() =>
  applications.value.filter((a) => ['applied', 'shortlisted', 'waiting'].includes(a.status)),
)

async function loadDrives() {
  const params = new URLSearchParams()
  if (search.value) params.set('q', search.value)
  if (eligibleOnly.value) params.set('eligible_only', 'true')
  drives.value = await api(`/api/student/drives?${params}`)
}

async function load() {
  loading.value = true
  try {
    const [p, a] = await Promise.all([
      api('/api/student/profile'),
      api('/api/student/applications'),
    ])
    profile.value = p
    applications.value = a
    await loadDrives()
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    loading.value = false
  }
}

async function apply(drive) {
  try {
    const data = await api(`/api/student/drives/${drive.id}/apply`, { method: 'POST' })
    notify(data.message)
    await load()
  } catch (err) {
    notify(err.message, 'danger')
  }
}

// ── User-triggered async export ──────────────────────────────────────
async function startExport() {
  exporting.value = true
  exportFile.value = ''
  try {
    const { task_id } = await api('/api/student/export', { method: 'POST' })
    notify('Export job queued — you will be alerted when it is ready', 'info')
    poll(task_id)
  } catch (err) {
    exporting.value = false
    notify(err.message, 'danger')
  }
}

function poll(taskId) {
  poller = setInterval(async () => {
    try {
      const data = await api(`/api/student/export/${taskId}`)
      if (data.state === 'SUCCESS') {
        clearInterval(poller)
        exporting.value = false
        exportFile.value = data.filename
        notify('Your CSV export is ready — check your email too', 'success')
      } else if (data.state === 'FAILURE') {
        clearInterval(poller)
        exporting.value = false
        notify('The export job failed', 'danger')
      }
    } catch {
      clearInterval(poller)
      exporting.value = false
    }
  }, 1500)
}

async function downloadExport() {
  await download(`/api/student/export/download/${exportFile.value}`, exportFile.value)
}

onMounted(load)
onUnmounted(() => clearInterval(poller))
</script>

<template>
  <div v-if="loading" class="text-center text-muted py-5">Loading…</div>

  <template v-else>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h3 class="mb-0">Welcome {{ profile.name }}</h3>
      <div class="text-muted small">
        {{ profile.roll_number }} · {{ profile.branch }} · CGPA {{ profile.cgpa }} · Year
        {{ profile.year }}
      </div>
    </div>

    <div v-if="profile.is_blacklisted" class="alert alert-danger">
      You have been <b>blacklisted</b> by the admin and cannot apply to drives.
    </div>
    <div v-if="!profile.resume_path" class="alert alert-warning py-2 small">
      You have not uploaded a resume yet.
      <router-link to="/student/profile">Upload one</router-link> so companies can review it.
    </div>

    <div class="row g-4">
      <!-- ── Available drives ──────────────────────────────────────── -->
      <div class="col-lg-8">
        <div class="card shadow-sm">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span class="fw-semibold">Approved Placement Drives</span>

            <div class="d-flex gap-2 align-items-center">
              <div class="form-check form-switch mb-0 small">
                <input
                  id="eligibleOnly"
                  v-model="eligibleOnly"
                  class="form-check-input"
                  type="checkbox"
                  @change="loadDrives"
                />
                <label class="form-check-label" for="eligibleOnly">Eligible only</label>
              </div>

              <div class="input-group input-group-sm" style="width: 220px">
                <input
                  v-model="search"
                  class="form-control"
                  placeholder="Search drives…"
                  @keyup.enter="loadDrives"
                />
                <button class="btn btn-outline-primary" @click="loadDrives">Search</button>
              </div>
            </div>
          </div>

          <div class="card-body">
            <div v-if="!drives.length" class="text-muted small">
              No open drives match your search.
            </div>

            <div
              v-for="d in drives"
              :key="d.id"
              class="border rounded p-3 mb-3 d-flex justify-content-between align-items-start"
            >
              <div>
                <div class="fw-semibold">
                  {{ d.job_title }}
                  <span class="text-muted fw-normal">· {{ d.company_name }}</span>
                </div>
                <div class="text-muted small mb-2">
                  {{ d.drive_name }} · {{ d.location || 'Location N/A' }} ·
                  ₹{{ d.salary.toLocaleString('en-IN') }}
                </div>
                <div class="small">
                  <span class="badge bg-light text-dark border me-1">
                    Branch: {{ d.eligible_branches }}
                  </span>
                  <span class="badge bg-light text-dark border me-1">
                    Min CGPA: {{ d.min_cgpa }}
                  </span>
                  <span class="badge bg-light text-dark border me-1">
                    Year: {{ d.eligible_year }}
                  </span>
                  <span class="badge bg-light text-dark border">
                    Deadline: {{ formatDate(d.deadline) }}
                  </span>
                </div>
                <div v-if="!d.eligible" class="text-danger small mt-2">
                  Not eligible — {{ d.ineligible_reason }}
                </div>
              </div>

              <div class="text-end ms-3" style="min-width: 130px">
                <router-link
                  class="btn btn-sm btn-outline-primary w-100 mb-2"
                  :to="`/student/drives/${d.id}`"
                >
                  View details
                </router-link>

                <button
                  v-if="d.already_applied"
                  class="btn btn-sm btn-secondary w-100"
                  disabled
                >
                  Applied
                </button>
                <button
                  v-else
                  class="btn btn-sm btn-success w-100"
                  :disabled="!d.eligible || profile.is_blacklisted"
                  @click="apply(d)"
                >
                  Apply
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Right rail ────────────────────────────────────────────── -->
      <div class="col-lg-4">
        <!-- Applied drives -->
        <div class="card shadow-sm mb-4">
          <div class="card-header fw-semibold">Applied Drives</div>
          <div class="table-responsive">
            <table class="table table-sm mb-0 align-middle">
              <thead class="table-light">
                <tr>
                  <th>Drive</th>
                  <th>Company</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!appliedDrives.length">
                  <td colspan="3" class="text-muted small">No active applications.</td>
                </tr>
                <tr v-for="a in appliedDrives" :key="a.id">
                  <td>{{ a.drive_name }}</td>
                  <td>{{ a.company_name }}</td>
                  <td>
                    <span :class="`badge bg-${statusColor(a.status)}`">{{ a.status }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="card-footer bg-white">
            <router-link class="btn btn-sm btn-outline-primary w-100" to="/student/history">
              View full application history
            </router-link>
          </div>
        </div>

        <!-- Async CSV export -->
        <div class="card shadow-sm">
          <div class="card-header fw-semibold">Export Placement History</div>
          <div class="card-body">
            <p class="text-muted small">
              Runs as a background job. You will get an email and an on-screen alert when the
              CSV is ready.
            </p>

            <button
              class="btn btn-outline-success w-100"
              :disabled="exporting || !applications.length"
              @click="startExport"
            >
              <span v-if="exporting" class="spinner-border spinner-border-sm me-2"></span>
              {{ exporting ? 'Exporting…' : 'Export as CSV' }}
            </button>

            <button
              v-if="exportFile"
              class="btn btn-success w-100 mt-2"
              @click="downloadExport"
            >
              Download {{ exportFile }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </template>
</template>
