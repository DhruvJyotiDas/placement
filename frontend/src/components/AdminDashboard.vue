<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, notify, formatDate, statusColor, initials, avatarColor } from '../api.js'

const stats = ref({})
const companies = ref([])
const students = ref([])
const drives = ref([])
const applications = ref([])

const search = ref('')
const loading = ref(true)
const sendingReport = ref(false)
const detail = ref(null)

// The wireframe splits companies into "Registered" vs "Company Applications".
const registeredCompanies = computed(() =>
  companies.value.filter((c) => c.approval_status === 'approved'),
)
const pendingCompanies = computed(() =>
  companies.value.filter((c) => c.approval_status === 'pending'),
)
const pendingDrives = computed(() => drives.value.filter((d) => d.status === 'pending'))
const ongoingDrives = computed(() => drives.value.filter((d) => d.status === 'approved'))

// Opens the shared detail modal using data already loaded — no extra API calls.
function showDetail(title, obj, keys) {
  const fields = {}
  keys.forEach((k) => (fields[k] = obj[k]))
  detail.value = { title, fields }
}

// ── Reports: aggregated purely from data already fetched by load() ────
const companyReport = computed(() => {
  const map = {}
  drives.value.forEach((d) => {
    map[d.company_name] ??= { company: d.company_name, drives: 0, applicants: 0, selected: 0 }
    map[d.company_name].drives++
    map[d.company_name].applicants += d.applicant_count
  })
  applications.value.forEach((a) => {
    if (a.status === 'selected') {
      map[a.company_name] ??= { company: a.company_name, drives: 0, applicants: 0, selected: 0 }
      map[a.company_name].selected++
    }
  })
  return Object.values(map)
})

const branchReport = computed(() => {
  const map = {}
  applications.value.forEach((a) => {
    const key = a.branch || 'Unknown'
    map[key] ??= { branch: key, applications: 0, selected: 0 }
    map[key].applications++
    if (a.status === 'selected') map[key].selected++
  })
  return Object.values(map)
})

async function load() {
  loading.value = true
  try {
    const q = search.value ? `?q=${encodeURIComponent(search.value)}` : ''
    const [s, c, st, d, a] = await Promise.all([
      api('/api/admin/stats'),
      api(`/api/admin/companies${q}`),
      api(`/api/admin/students${q}`),
      api(`/api/admin/drives${q}`),
      api(`/api/admin/applications${q}`),
    ])
    stats.value = s
    companies.value = c
    students.value = st
    drives.value = d
    applications.value = a
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    loading.value = false
  }
}

async function sendReport() {
  sendingReport.value = true
  try {
    const data = await api('/api/admin/report', { method: 'POST' })
    notify(data.message)
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    sendingReport.value = false
  }
}

async function act(path, confirmMessage, method = 'PUT') {
  if (confirmMessage && !confirm(confirmMessage)) return
  try {
    const data = await api(path, { method })
    notify(data.message)
    await load()
  } catch (err) {
    notify(err.message, 'danger')
  }
}

onMounted(load)
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h3 class="mb-0">Welcome Admin</h3>

    <div class="d-flex gap-2">
      <div class="input-group" style="max-width: 420px">
        <input
          v-model="search"
          class="form-control"
          placeholder="Search students, companies, drives…"
          @keyup.enter="load"
        />
        <button class="btn btn-primary" @click="load">Search</button>
        <button v-if="search" class="btn btn-outline-secondary" @click="search = ''; load()">
          Clear
        </button>
      </div>

      <button
        class="btn btn-outline-dark"
        :disabled="sendingReport"
        @click="sendReport"
        title="Also runs automatically on the 1st of every month"
      >
        {{ sendingReport ? 'Sending…' : 'Send Monthly Report Now' }}
      </button>
    </div>
  </div>

  <!-- Headline counts -->
  <div class="row g-3 mb-4">
    <div v-for="card in [
        { label: 'Total Students', value: stats.total_students, color: 'primary' },
        { label: 'Total Companies', value: stats.total_companies, color: 'info' },
        { label: 'Total Drives', value: stats.total_drives, color: 'dark' },
        { label: 'Applications', value: stats.total_applications, color: 'secondary' },
        { label: 'Students Selected', value: stats.students_selected, color: 'success' },
      ]"
      :key="card.label"
      class="col"
    >
      <div class="card text-center shadow-sm h-100">
        <div class="card-body">
          <div :class="`display-6 text-${card.color}`">{{ card.value ?? '–' }}</div>
          <div class="text-muted small">{{ card.label }}</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Selection funnel -->
  <div v-if="stats.total_applications" class="mb-4">
    <div class="d-flex justify-content-between small text-muted mb-1">
      <span>Applications converted to selections</span>
      <span>{{ stats.students_selected }} / {{ stats.total_applications }}</span>
    </div>
    <div class="progress" style="height: 8px">
      <div
        class="progress-bar bg-success"
        :style="`width: ${(100 * stats.students_selected) / stats.total_applications}%`"
      ></div>
    </div>
  </div>

  <div v-if="loading" class="text-center text-muted py-5">Loading…</div>

  <template v-else>
    <ul class="nav nav-tabs" role="tablist">
      <li class="nav-item">
        <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-companies" type="button">
          Companies
          <span v-if="pendingCompanies.length" class="badge rounded-pill bg-warning text-dark ms-1">
            {{ pendingCompanies.length }}
          </span>
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-students" type="button">
          Students <span class="badge rounded-pill bg-light text-dark ms-1">{{ students.length }}</span>
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-drives" type="button">
          Drives
          <span v-if="pendingDrives.length" class="badge rounded-pill bg-warning text-dark ms-1">
            {{ pendingDrives.length }}
          </span>
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-applications" type="button">
          Applications
          <span class="badge rounded-pill bg-light text-dark ms-1">{{ applications.length }}</span>
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-reports" type="button">
          Reports
        </button>
      </li>
    </ul>

    <div class="tab-content bg-white border border-top-0 rounded-bottom p-3 shadow-sm">
      <!-- ── Companies tab ───────────────────────────────────────────── -->
      <div class="tab-pane fade show active" id="tab-companies">
        <div class="row g-4">
          <div class="col-lg-6">
            <div class="card shadow-sm">
              <div class="card-header fw-semibold">
                Company Applications
                <span class="badge bg-warning text-dark ms-2">{{ pendingCompanies.length }}</span>
              </div>
              <ul class="list-group list-group-flush">
                <li v-if="!pendingCompanies.length" class="list-group-item text-muted small">
                  No pending company registrations.
                </li>
                <li
                  v-for="c in pendingCompanies"
                  :key="c.id"
                  class="list-group-item d-flex justify-content-between align-items-center"
                >
                  <div class="d-flex align-items-center gap-2">
                    <div class="avatar-circle" :style="`background:${avatarColor(c.company_name)}`">
                      {{ initials(c.company_name) }}
                    </div>
                    <div>
                      <div class="fw-semibold">{{ c.company_name }}</div>
                      <div class="text-muted small">{{ c.email }} · {{ c.hr_contact }}</div>
                    </div>
                  </div>
                  <div class="btn-group btn-group-sm">
                    <button
                      class="btn btn-outline-secondary"
                      @click="showDetail(c.company_name, c, ['email','hr_contact','website','industry','location','description','approval_status'])"
                    >
                      View
                    </button>
                    <button
                      class="btn btn-outline-success"
                      @click="act(`/api/admin/companies/${c.id}/approve`)"
                    >
                      Approve
                    </button>
                    <button
                      class="btn btn-outline-danger"
                      @click="act(`/api/admin/companies/${c.id}/reject`)"
                    >
                      Reject
                    </button>
                  </div>
                </li>
              </ul>
            </div>
          </div>

          <div class="col-lg-6">
            <div class="card shadow-sm">
              <div class="card-header fw-semibold">Registered Companies</div>
              <ul class="list-group list-group-flush">
                <li v-if="!registeredCompanies.length" class="list-group-item text-muted small">
                  No approved companies yet.
                </li>
                <li
                  v-for="c in registeredCompanies"
                  :key="c.id"
                  class="list-group-item d-flex justify-content-between align-items-center"
                >
                  <div class="d-flex align-items-center gap-2">
                    <div class="avatar-circle" :style="`background:${avatarColor(c.company_name)}`">
                      {{ initials(c.company_name) }}
                    </div>
                    <div>
                      <span class="fw-semibold">{{ c.company_name }}</span>
                      <span v-if="c.is_blacklisted" class="badge bg-danger ms-2">Blacklisted</span>
                      <div class="text-muted small">{{ c.drive_count }} drive(s)</div>
                    </div>
                  </div>
                  <div class="btn-group btn-group-sm">
                    <button
                      class="btn btn-outline-secondary"
                      @click="showDetail(c.company_name, c, ['email','hr_contact','website','industry','location','description','drive_count','is_blacklisted'])"
                    >
                      View
                    </button>
                    <button
                      v-if="!c.is_blacklisted"
                      class="btn btn-outline-danger"
                      @click="act(
                        `/api/admin/companies/${c.id}/blacklist`,
                        `Blacklist ${c.company_name}? All of its drives will be cancelled.`,
                      )"
                    >
                      Blacklist
                    </button>
                    <button
                      v-else
                      class="btn btn-outline-secondary"
                      @click="act(`/api/admin/companies/${c.id}/unblacklist`)"
                    >
                      Restore
                    </button>
                    <button
                      class="btn btn-outline-danger"
                      @click="act(
                        `/api/admin/companies/${c.id}`,
                        `Permanently remove ${c.company_name}? This cannot be undone.`,
                        'DELETE',
                      )"
                    >
                      Remove
                    </button>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Students tab ────────────────────────────────────────────── -->
      <div class="tab-pane fade" id="tab-students">
        <div class="card shadow-sm">
          <div class="card-header fw-semibold">Registered Students</div>
          <ul class="list-group list-group-flush">
            <li v-if="!students.length" class="list-group-item text-muted small">
              No students registered.
            </li>
            <li
              v-for="s in students"
              :key="s.id"
              class="list-group-item d-flex justify-content-between align-items-center"
            >
              <div class="d-flex align-items-center gap-2">
                <div class="avatar-circle" :style="`background:${avatarColor(s.name)}`">
                  {{ initials(s.name) }}
                </div>
                <div>
                  <span class="fw-semibold">{{ s.name }}</span>
                  <span v-if="s.is_blacklisted" class="badge bg-danger ms-2">Blacklisted</span>
                  <div class="text-muted small">
                    {{ s.roll_number }} · {{ s.branch }} · CGPA {{ s.cgpa }} · Year {{ s.year }}
                  </div>
                </div>
              </div>
              <div class="btn-group btn-group-sm">
                <button
                  class="btn btn-outline-secondary"
                  @click="showDetail(s.name, s, ['email','roll_number','branch','cgpa','year','skills','resume_path','is_blacklisted'])"
                >
                  View
                </button>
                <button
                  v-if="!s.is_blacklisted"
                  class="btn btn-outline-danger"
                  @click="act(
                    `/api/admin/students/${s.id}/blacklist`,
                    `Blacklist and deactivate ${s.name}?`,
                  )"
                >
                  Blacklist
                </button>
                <button
                  v-else
                  class="btn btn-outline-secondary"
                  @click="act(`/api/admin/students/${s.id}/unblacklist`)"
                >
                  Restore
                </button>
                <button
                  class="btn btn-outline-danger"
                  @click="act(
                    `/api/admin/students/${s.id}`,
                    `Permanently remove ${s.name}? This cannot be undone.`,
                    'DELETE',
                  )"
                >
                  Remove
                </button>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- ── Drives tab ──────────────────────────────────────────────── -->
      <div class="tab-pane fade" id="tab-drives">
        <div class="card shadow-sm mb-4">
          <div class="card-header fw-semibold">
            Drive Approvals
            <span class="badge bg-warning text-dark ms-2">{{ pendingDrives.length }}</span>
          </div>
          <div class="table-responsive">
            <table class="table table-sm mb-0 align-middle">
              <thead class="table-light">
                <tr>
                  <th>Sr No.</th>
                  <th>Drive Name</th>
                  <th>Company</th>
                  <th>Deadline</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!pendingDrives.length">
                  <td colspan="5" class="text-muted small">No drives awaiting approval.</td>
                </tr>
                <tr v-for="(d, i) in pendingDrives" :key="d.id">
                  <td>{{ i + 1 }}</td>
                  <td>
                    {{ d.drive_name }}
                    <div class="text-muted small">{{ d.job_title }}</div>
                  </td>
                  <td>{{ d.company_name }}</td>
                  <td>{{ formatDate(d.deadline) }}</td>
                  <td>
                    <div class="btn-group btn-group-sm">
                      <button
                        class="btn btn-outline-secondary"
                        @click="showDetail(d.drive_name, d, ['company_name','job_title','job_description','skills_required','experience_required','benefits','eligible_branches','min_cgpa','eligible_year','salary','location','status'])"
                      >
                        View
                      </button>
                      <button
                        class="btn btn-outline-success"
                        @click="act(`/api/admin/drives/${d.id}/approve`)"
                      >
                        Approve
                      </button>
                      <button
                        class="btn btn-outline-danger"
                        @click="act(`/api/admin/drives/${d.id}/reject`)"
                      >
                        Reject
                      </button>
                      <button
                        class="btn btn-outline-danger"
                        @click="act(
                          `/api/admin/drives/${d.id}`,
                          `Permanently remove drive '${d.drive_name}'? This cannot be undone.`,
                          'DELETE',
                        )"
                      >
                        Remove
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card shadow-sm">
          <div class="card-header fw-semibold">Ongoing Drives</div>
          <div class="table-responsive">
            <table class="table table-sm mb-0 align-middle">
              <thead class="table-light">
                <tr>
                  <th>Sr No.</th>
                  <th>Drive Name</th>
                  <th>Company</th>
                  <th>Applicants</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!ongoingDrives.length">
                  <td colspan="5" class="text-muted small">No ongoing drives.</td>
                </tr>
                <tr v-for="(d, i) in ongoingDrives" :key="d.id">
                  <td>{{ 1000 + d.id }}</td>
                  <td>{{ d.drive_name }}</td>
                  <td>{{ d.company_name }}</td>
                  <td>{{ d.applicant_count }}</td>
                  <td>
                    <div class="btn-group btn-group-sm">
                      <button
                        class="btn btn-outline-secondary"
                        @click="showDetail(d.drive_name, d, ['company_name','job_title','job_description','skills_required','experience_required','benefits','eligible_branches','min_cgpa','eligible_year','salary','location','applicant_count','status'])"
                      >
                        View
                      </button>
                      <button
                        class="btn btn-outline-secondary"
                        @click="act(`/api/admin/drives/${d.id}/close`)"
                      >
                        Mark as complete
                      </button>
                      <button
                        class="btn btn-outline-danger"
                        @click="act(
                          `/api/admin/drives/${d.id}`,
                          `Permanently remove drive '${d.drive_name}'? This cannot be undone.`,
                          'DELETE',
                        )"
                      >
                        Remove
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ── Applications tab ────────────────────────────────────────── -->
      <div class="tab-pane fade" id="tab-applications">
        <div class="card shadow-sm">
          <div class="card-header fw-semibold">Student Applications</div>
          <div class="table-responsive" style="max-height: 480px; overflow-y: auto">
            <table class="table table-sm mb-0 align-middle">
              <thead class="table-light">
                <tr>
                  <th>Sr No.</th>
                  <th>Name</th>
                  <th>Drive</th>
                  <th>Company</th>
                  <th>Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!applications.length">
                  <td colspan="6" class="text-muted small">No applications yet.</td>
                </tr>
                <tr v-for="(a, i) in applications" :key="a.id">
                  <td>{{ i + 1 }}</td>
                  <td>{{ a.student_name }}</td>
                  <td>{{ a.drive_name }}</td>
                  <td>{{ a.company_name }}</td>
                  <td>{{ formatDate(a.application_date) }}</td>
                  <td>
                    <span :class="`badge bg-${statusColor(a.status)}`">{{ a.status }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ── Reports tab ─────────────────────────────────────────────── -->
      <div class="tab-pane fade" id="tab-reports">
        <div class="row g-4">
          <div class="col-lg-6">
            <div class="card shadow-sm">
              <div class="card-header fw-semibold">Placements by Company</div>
              <div class="table-responsive">
                <table class="table table-sm mb-0 align-middle">
                  <thead class="table-light">
                    <tr>
                      <th>Company</th>
                      <th>Drives</th>
                      <th>Applicants</th>
                      <th>Selected</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="!companyReport.length">
                      <td colspan="4" class="text-muted small">No data yet.</td>
                    </tr>
                    <tr v-for="row in companyReport" :key="row.company">
                      <td>{{ row.company }}</td>
                      <td>{{ row.drives }}</td>
                      <td>{{ row.applicants }}</td>
                      <td>{{ row.selected }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div class="col-lg-6">
            <div class="card shadow-sm">
              <div class="card-header fw-semibold">Applications by Branch</div>
              <div class="table-responsive">
                <table class="table table-sm mb-0 align-middle">
                  <thead class="table-light">
                    <tr>
                      <th>Branch</th>
                      <th>Applications</th>
                      <th>Selected</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="!branchReport.length">
                      <td colspan="3" class="text-muted small">No data yet.</td>
                    </tr>
                    <tr v-for="row in branchReport" :key="row.branch">
                      <td>{{ row.branch }}</td>
                      <td>{{ row.applications }}</td>
                      <td>{{ row.selected }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <div class="alert alert-info py-2 small mt-3 mb-0">
          For a full institute-wide HTML report emailed to you, use "Send Monthly Report Now" above.
        </div>
      </div>
    </div>
  </template>

  <!-- ── Shared detail modal — populated from data already loaded, no extra API calls ── -->
  <div v-if="detail" class="modal d-block" style="background: rgba(0, 0, 0, 0.5)" @click.self="detail = null">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ detail.title }}</h5>
          <button class="btn-close" @click="detail = null"></button>
        </div>
        <div class="modal-body">
          <dl class="row mb-0">
            <template v-for="(value, key) in detail.fields" :key="key">
              <dt class="col-5 text-capitalize">{{ key.replaceAll('_', ' ') }}</dt>
              <dd class="col-7">{{ value === null || value === '' ? '—' : value }}</dd>
            </template>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>
