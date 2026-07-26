import { reactive } from 'vue'

/** Auth state, restored from localStorage so a refresh keeps you logged in. */
export const auth = reactive({
  token: localStorage.getItem('token') || '',
  role: localStorage.getItem('role') || '',
  email: localStorage.getItem('email') || '',

  get isLoggedIn() {
    return !!this.token
  },

  login({ token, role, email }) {
    this.token = token
    this.role = role
    this.email = email
    localStorage.setItem('token', token)
    localStorage.setItem('role', role)
    localStorage.setItem('email', email)
  },

  logout() {
    this.token = ''
    this.role = ''
    this.email = ''
    localStorage.clear()
  },
})

/** Toast messages shown by App.vue. */
export const toasts = reactive({ items: [] })

export function notify(message, variant = 'success') {
  const id = Date.now() + Math.random()
  toasts.items.push({ id, message, variant })
  setTimeout(() => {
    const i = toasts.items.findIndex((t) => t.id === id)
    if (i !== -1) toasts.items.splice(i, 1)
  }, 4000)
}

/**
 * Thin fetch wrapper: attaches the JWT, parses JSON, and surfaces
 * the backend's `message` field on failure.
 */
export async function api(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = {}
  if (auth.token) headers.Authorization = `Bearer ${auth.token}`
  if (!isForm) headers['Content-Type'] = 'application/json'

  const response = await fetch(path, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  })

  // An expired or invalid token means the session is over.
  if (response.status === 401) {
    auth.logout()
    window.location.hash = '/login'
    throw new Error('Your session expired. Please log in again.')
  }

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.message || `Request failed (${response.status})`)
  }
  return data
}

/** Download a protected file (resume / CSV export) with the JWT attached. */
export async function download(path, filename) {
  const response = await fetch(path, {
    headers: { Authorization: `Bearer ${auth.token}` },
  })
  if (!response.ok) throw new Error('Download failed')

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export const formatDate = (iso) =>
  new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })

export const statusColor = (status) =>
  ({
    approved: 'success',
    selected: 'success',
    shortlisted: 'info',
    applied: 'primary',
    pending: 'warning',
    waiting: 'warning',
    rejected: 'danger',
    cancelled: 'danger',
    closed: 'secondary',
  })[status] || 'secondary'

/** Up to two initials for an avatar badge, e.g. "Test Exporter" -> "TE". */
export const initials = (name) =>
  (name || '?')
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

const AVATAR_COLORS = ['#6366f1', '#0ea5e9', '#16a34a', '#f59e0b', '#dc2626', '#8b5cf6', '#0d9488']

/** A stable colour for a name, so the same person always gets the same avatar colour. */
export const avatarColor = (name) => {
  let hash = 0
  for (const ch of name || '') hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}
