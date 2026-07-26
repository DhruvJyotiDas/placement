<script setup>
import { useRouter } from 'vue-router'
import { auth, toasts } from './api.js'

const router = useRouter()

const roleLabel = { admin: 'Admin', company: 'Company', student: 'Student' }

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <nav v-if="auth.isLoggedIn" class="navbar navbar-expand navbar-dark bg-dark px-4 shadow-sm sticky-top">
    <span class="navbar-brand fw-bold">Placement Portal</span>

    <div class="navbar-nav me-auto">
      <router-link class="nav-link" :to="`/${auth.role}`">Dashboard</router-link>
      <template v-if="auth.role === 'student'">
        <router-link class="nav-link" to="/student/profile">Edit Profile</router-link>
        <router-link class="nav-link" to="/student/history">History</router-link>
      </template>
    </div>

    <span class="navbar-text me-3">
      <span class="badge bg-secondary me-2">{{ roleLabel[auth.role] }}</span>
      {{ auth.email }}
    </span>
    <button class="btn btn-outline-light btn-sm" @click="logout">Logout</button>
  </nav>

  <main class="container-fluid px-4 py-4">
    <router-view />
  </main>

  <!-- Toasts: success/error feedback, and the "export ready" alert -->
  <div class="toast-container position-fixed bottom-0 end-0 p-3">
    <div
      v-for="toast in toasts.items"
      :key="toast.id"
      class="toast show align-items-center text-white border-0 mb-2"
      :class="`bg-${toast.variant}`"
    >
      <div class="d-flex">
        <div class="toast-body">{{ toast.message }}</div>
      </div>
    </div>
  </div>
</template>
