// ── API Client ────────────────────────────────────────────────────────────────
import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: BASE, timeout: 30000 })

api.interceptors.request.use((cfg) => {
  const tok = localStorage.getItem('nf_token')
  if (tok) cfg.headers.Authorization = `Bearer ${tok}`
  return cfg
})

api.interceptors.response.use(
  (r) => r,
  (e) => {
    if (e.response?.status === 401) {
      localStorage.removeItem('nf_token')
      localStorage.removeItem('nf_user')
      window.location.href = '/login'
    }
    return Promise.reject(e)
  }
)

// ── API Functions ─────────────────────────────────────────────────────────────
export const authApi = {
  login: (username: string, password: string) => {
    const fd = new FormData()
    fd.append('username', username)
    fd.append('password', password)
    return api.post('/api/auth/login', fd)
  },
  register: (d: any) => api.post('/api/auth/register', d),
  me: () => api.get('/api/auth/me'),
}

export const reviewsApi = {
  list: (p?: any) => api.get('/api/reviews/', { params: p }),
  get: (id: number) => api.get(`/api/reviews/${id}`),
  create: (title: string, files: File[], repoId?: number) => {
    const fd = new FormData()
    fd.append('title', title)
    files.forEach((f) => fd.append('files', f))
    if (repoId) fd.append('repository_id', String(repoId))
    return api.post('/api/reviews/', fd)
  },
  delete: (id: number) => api.delete(`/api/reviews/${id}`),
}

export const issuesApi = {
  byReview: (id: number, p?: any) => api.get(`/api/issues/review/${id}`, { params: p }),
  acknowledge: (id: number) => api.patch(`/api/issues/${id}/acknowledge`),
}

export const analyticsApi = {
  dashboard: () => api.get('/api/analytics/dashboard'),
  global: () => api.get('/api/analytics/global'),
}

export const usersApi = {
  leaderboard: () => api.get('/api/users/leaderboard'),
  profile: (username: string) => api.get(`/api/users/${username}/profile`),
}

export const reposApi = {
  list: () => api.get('/api/repos/'),
  create: (d: any) => api.post('/api/repos/', d),
}

// ── Types ─────────────────────────────────────────────────────────────────────
export type Severity = 'critical' | 'error' | 'warning' | 'info'
export type Category = 'security' | 'complexity' | 'style' | 'performance' | 'maintainability' | 'bug' | 'documentation' | 'duplication'
export type ReviewStatus = 'pending' | 'analyzing' | 'complete' | 'failed'

export interface Review {
  id: number
  title: string
  status: ReviewStatus
  quality_score: number | null
  maintainability_index: number | null
  total_issues: number
  critical_issues: number
  error_issues: number
  warning_issues: number
  info_issues: number
  total_lines: number
  total_files: number
  avg_complexity: number | null
  duplication_pct: number | null
  ai_summary: string | null
  ai_praise: string | null
  ai_top_priority: string | null
  analysis_duration_ms: number | null
  created_at: string
  completed_at: string | null
  files?: ReviewFile[]
}

export interface ReviewFile {
  id: number
  filename: string
  language: string
  lines_of_code: number
  blank_lines: number
  comment_lines: number
  cyclomatic_complexity: number | null
  cognitive_complexity: number | null
  maintainability_index: number | null
  halstead_volume: number | null
  issue_count: number
  quality_score: number | null
  annotations: Record<string, string[]>
  content: string
  issues: Issue[]
}

export interface Issue {
  id: number
  severity: Severity
  category: Category
  rule_id: string
  title: string
  message: string
  line_start: number | null
  line_end: number | null
  column_start: number | null
  code_snippet: string | null
  is_fixable: boolean
  fix_description: string | null
  fix_code_snippet: string | null
  is_acknowledged: boolean
  suggestions: Suggestion[]
}

export interface Suggestion {
  id: number
  title: string
  explanation: string
  before_code: string | null
  after_code: string | null
  confidence: number
  is_applied: boolean
}

export interface Badge {
  slug: string
  name: string
  icon: string
  description: string
  color: string
  earned_at?: string
}
