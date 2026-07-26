<script setup>
import { onMounted, ref } from 'vue'
import { api, notify, formatDate, statusColor, initials, avatarColor } from '../api.js'

const profile = ref({})
const upcoming = ref([])
const closed = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const [p, d] = await Promise.all([api('/api/company/profile'), api('/api/company/drives')])
    profile.value = p
    upcoming.value = d.upcoming
    closed.value = d.closed
  } catch (err) {
    notify(err.message, 'danger')
  } finally {
    loading.value = false
  }
}

async function markComplete(drive) {
  if (!confirm(`Mark "${drive.drive_name}" as complete? It will stop accepting applications.`))
    return
  try {
    const data = await api(`/api/company/drives/${drive.id}/complete`, { method: 'PUT' })
    notify(data.message)
    await load()
  } catch (err) {
    notify(err.message, 'danger')
  }
}

onMounted(load)
</script>

<template>
  <div v-if="loading" class="text-center text-muted py-5">Loading…</div>

  <template v-else>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h3 class="mb-0">Welcome {{ profile.company_name }}</h3>
      <router-link
        v-if="profile.approval_status === 'approved' && !profile.is_blacklisted"
        class="btn btn-success"
        to="/company/drives/new"
      >
        Create Drive
      </router-link>
    </div>

    <!-- Approval gate: no drives until the admin says so -->
    <div v-if="profile.is_blacklisted" class="alert alert-danger">
      Your company has been <b>blacklisted</b> by the admin. All of your drives were cancelled
      and you cannot create new ones.
    </div>
    <div v-else-if="profile.approval_status === 'pending'" class="alert alert-warning">
      Your company registration is <b>pending admin approval</b>. You will be able to create
      placement drives once it is approved.
    </div>
    <div v-else-if="profile.approval_status === 'rejected'" class="alert alert-danger">
      Your company registration was <b>rejected</b> by the admin.
    </div>

    <div class="row g-4">
      <!-- Company details -->
      <div class="col-lg-4">
        <div class="card shadow-sm h-100">
          <div class="card-header fw-semibold">Company Details</div>
          <div class="card-body">
            <div class="d-flex align-items-center gap-3 mb-3">
              <div
                class="avatar-circle"
                style="width: 52px; height: 52px; font-size: 1.1rem"
                :style="`background:${avatarColor(profile.company_name)}`"
              >
                {{ initials(profile.company_name) }}
              </div>
              <div>
                <div class="fw-semibold">{{ profile.company_name }}</div>
                <span :class="`badge bg-${statusColor(profile.approval_status)}`">
                  {{ profile.approval_status }}
                </span>
              </div>
            </div>

            <dl class="row mb-0 small">
              <dt class="col-5">HR Contact</dt>
              <dd class="col-7">{{ profile.hr_contact || '—' }}</dd>

              <dt class="col-5">Website</dt>
              <dd class="col-7">
                <a v-if="profile.website" :href="profile.website" target="_blank">
                  {{ profile.website }}
                </a>
                <span v-else>—</span>
              </dd>

              <dt class="col-5">Email</dt>
              <dd class="col-7">{{ profile.email }}</dd>
            </dl>

            <hr />
            <p class="text-muted small mb-0">{{ profile.description || 'No overview provided.' }}</p>
          </div>
        </div>
      </div>

      <!-- Drives -->
      <div class="col-lg-8">
        <ul class="nav nav-tabs" role="tablist">
          <li class="nav-item">
            <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-upcoming" type="button">
              Upcoming Drives
              <span class="badge rounded-pill bg-light text-dark ms-1">{{ upcoming.length }}</span>
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-closed" type="button">
              Closed Drives
              <span class="badge rounded-pill bg-light text-dark ms-1">{{ closed.length }}</span>
            </button>
          </li>
        </ul>

        <div class="tab-content bg-white border border-top-0 rounded-bottom shadow-sm">
          <div class="tab-pane fade show active" id="tab-upcoming">
            <div class="table-responsive">
              <table class="table table-sm mb-0 align-middle">
                <thead class="table-light">
                  <tr>
                    <th>Sr No.</th>
                    <th>Drive Name</th>
                    <th>Status</th>
                    <th>Applicants</th>
                    <th>Deadline</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!upcoming.length">
                    <td colspan="6" class="text-muted small">
                      No drives yet.
                      <router-link
                        v-if="profile.approval_status === 'approved'"
                        to="/company/drives/new"
                      >
                        Create one.
                      </router-link>
                    </td>
                  </tr>
                  <tr v-for="d in upcoming" :key="d.id">
                    <td>{{ 1000 + d.id }}</td>
                    <td>
                      {{ d.drive_name }}
                      <div class="text-muted small">{{ d.job_title }}</div>
                    </td>
                    <td>
                      <span :class="`badge bg-${statusColor(d.status)}`">{{ d.status }}</span>
                    </td>
                    <td>{{ d.applicant_count }}</td>
                    <td>{{ formatDate(d.deadline) }}</td>
                    <td>
                      <div class="btn-group btn-group-sm">
                        <router-link
                          class="btn btn-outline-primary"
                          :to="`/company/drives/${d.id}/applications`"
                        >
                          View details
                        </router-link>
                        <button class="btn btn-outline-success" @click="markComplete(d)">
                          Mark as complete
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="tab-pane fade" id="tab-closed">
            <div class="table-responsive">
              <table class="table table-sm mb-0 align-middle">
                <thead class="table-light">
                  <tr>
                    <th>Sr No.</th>
                    <th>Drive Name</th>
                    <th>Status</th>
                    <th>Applicants</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!closed.length">
                    <td colspan="5" class="text-muted small">No closed drives.</td>
                  </tr>
                  <tr v-for="d in closed" :key="d.id">
                    <td>{{ 1000 + d.id }}</td>
                    <td>{{ d.drive_name }}</td>
                    <td>
                      <span :class="`badge bg-${statusColor(d.status)}`">{{ d.status }}</span>
                    </td>
                    <td>{{ d.applicant_count }}</td>
                    <td>
                      <router-link
                        class="btn btn-sm btn-outline-primary"
                        :to="`/company/drives/${d.id}/applications`"
                      >
                        Update
                      </router-link>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
</template>
