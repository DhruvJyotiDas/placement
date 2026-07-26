import { createRouter, createWebHashHistory } from 'vue-router'

import { auth } from '../api.js'

import LoginForm from '../components/LoginForm.vue'
import RegisterForm from '../components/RegisterForm.vue'
import AdminDashboard from '../components/AdminDashboard.vue'
import CompanyDashboard from '../components/CompanyDashboard.vue'
import CreateDrive from '../components/CreateDrive.vue'
import DriveApplications from '../components/DriveApplications.vue'
import ApplicationReview from '../components/ApplicationReview.vue'
import StudentDashboard from '../components/StudentDashboard.vue'
import StudentProfile from '../components/StudentProfile.vue'
import DriveDetail from '../components/DriveDetail.vue'
import CompanyDetail from '../components/CompanyDetail.vue'
import ApplicationHistory from '../components/ApplicationHistory.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginForm, meta: { guest: true } },
  { path: '/register', component: RegisterForm, meta: { guest: true } },

  // Admin
  { path: '/admin', component: AdminDashboard, meta: { role: 'admin' } },

  // Company
  { path: '/company', component: CompanyDashboard, meta: { role: 'company' } },
  { path: '/company/drives/new', component: CreateDrive, meta: { role: 'company' } },
  {
    path: '/company/drives/:id/applications',
    component: DriveApplications,
    meta: { role: 'company' },
  },
  {
    path: '/company/applications/:id',
    component: ApplicationReview,
    meta: { role: 'company' },
  },

  // Student
  { path: '/student', component: StudentDashboard, meta: { role: 'student' } },
  { path: '/student/profile', component: StudentProfile, meta: { role: 'student' } },
  { path: '/student/history', component: ApplicationHistory, meta: { role: 'student' } },
  { path: '/student/drives/:id', component: DriveDetail, meta: { role: 'student' } },
  { path: '/student/companies/:id', component: CompanyDetail, meta: { role: 'student' } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

const homeFor = (role) => `/${role}`

/** Role-based route guard — the client-side half of the RBAC. */
router.beforeEach((to) => {
  if (to.meta.role) {
    if (!auth.isLoggedIn) return '/login'
    if (auth.role !== to.meta.role) return homeFor(auth.role)
  }
  if (to.meta.guest && auth.isLoggedIn) return homeFor(auth.role)
  return true
})

export default router
