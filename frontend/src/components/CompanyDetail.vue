<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, notify, formatDate, initials, avatarColor } from '../api.js'

const route = useRoute()
const router = useRouter()

const company = ref(null)
const drives = ref([])
const loading = ref(true)

async function load() {
  try {
    const data = await api(`/api/student/companies/${route.params.id}`)
    company.value = data.company
    drives.value = data.drives
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

  <div v-else-if="company" class="row justify-content-center">
    <div class="col-lg-8">
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><router-link to="/student">Dashboard</router-link></li>
          <li class="breadcrumb-item active" aria-current="page">{{ company.company_name }}</li>
        </ol>
      </nav>

      <div class="card shadow-sm">
        <div class="card-header d-flex justify-content-between align-items-center">
          <div class="d-flex align-items-center gap-2">
            <div
              class="avatar-circle"
              style="width: 32px; height: 32px; font-size: 0.75rem"
              :style="`background:${avatarColor(company.company_name)}`"
            >
              {{ initials(company.company_name) }}
            </div>
            <span class="fw-semibold">{{ company.company_name }}</span>
          </div>
          <button class="btn btn-sm btn-outline-secondary" @click="router.back()">Back</button>
        </div>

        <div class="card-body p-4">
          <h6 class="text-muted">Overview</h6>
          <p>{{ company.description || 'This company has not provided an overview.' }}</p>

          <dl class="row small">
            <dt class="col-sm-3">Website</dt>
            <dd class="col-sm-9">
              <a v-if="company.website" :href="company.website" target="_blank">
                {{ company.website }}
              </a>
              <span v-else>—</span>
            </dd>

            <dt class="col-sm-3">HR Contact</dt>
            <dd class="col-sm-9">{{ company.hr_contact || '—' }}</dd>
          </dl>

          <hr />

          <h6 class="text-muted mb-3">Current Drives</h6>

          <div v-if="!drives.length" class="text-muted small">
            This company has no open drives right now.
          </div>

          <div
            v-for="d in drives"
            :key="d.id"
            class="border rounded p-3 mb-2 d-flex justify-content-between align-items-center"
          >
            <div>
              <div class="fw-semibold">{{ d.drive_name }}</div>
              <div class="text-muted small">
                {{ d.job_title }} · Deadline {{ formatDate(d.deadline) }}
              </div>
            </div>
            <router-link
              class="btn btn-sm btn-outline-primary"
              :to="`/student/drives/${d.id}`"
            >
              View details
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
