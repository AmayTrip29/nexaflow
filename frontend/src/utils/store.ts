// ── Store ─────────────────────────────────────────────────────────────────────
import { create } from 'zustand'

interface AppState {
  user: any | null
  token: string | null
  setUser: (user: any, token: string) => void
  logout: () => void
  analysisProgress: number
  analysisMessage: string
  setAnalysisProgress: (p: number, m: string) => void
}

export const useStore = create<AppState>((set) => ({
  user: JSON.parse(localStorage.getItem('nf_user') || 'null'),
  token: localStorage.getItem('nf_token'),
  setUser: (user, token) => {
    localStorage.setItem('nf_user', JSON.stringify(user))
    localStorage.setItem('nf_token', token)
    set({ user, token })
  },
  logout: () => {
    localStorage.removeItem('nf_user')
    localStorage.removeItem('nf_token')
    set({ user: null, token: null })
  },
  analysisProgress: 0,
  analysisMessage: '',
  setAnalysisProgress: (p, m) => set({ analysisProgress: p, analysisMessage: m }),
}))

// ── Helpers ───────────────────────────────────────────────────────────────────
import type { Severity } from './api'

export const severityColor = (s: Severity): string => ({
  critical: '#ff4d6d', error: '#ff7c00', warning: '#ffb830', info: '#38bdf8',
}[s] || '#9090c0')

export const severityBg = (s: Severity): string => ({
  critical: 'sev-critical', error: 'sev-error', warning: 'sev-warning', info: 'sev-info',
}[s] || 'sev-info')

export const scoreColor = (score: number): string => {
  if (score >= 80) return '#22d3a0'
  if (score >= 60) return '#ffb830'
  if (score >= 40) return '#ff7c00'
  return '#ff4d6d'
}

export const scoreLabel = (score: number): string => {
  if (score >= 85) return 'Excellent'
  if (score >= 70) return 'Good'
  if (score >= 55) return 'Fair'
  if (score >= 40) return 'Poor'
  return 'Critical'
}

export const categoryIcon = (cat: string): string => ({
  security: '🔒', complexity: '🔀', style: '✏️', performance: '⚡',
  maintainability: '🔧', bug: '🐛', documentation: '📄', duplication: '📋',
}[cat] || '⚠️')

export const langIcon = (lang: string): string => ({
  python: '🐍', javascript: '📜', typescript: '🔷', java: '☕',
  cpp: '⚙️', c: '🔩', go: '🐹', rust: '🦀', unknown: '📄',
}[lang] || '📄')

export const timeAgo = (d: string): string => {
  const diff = Date.now() - new Date(d).getTime()
  const m = Math.floor(diff / 60000)
  const h = Math.floor(m / 60)
  const days = Math.floor(h / 24)
  if (days > 0) return `${days}d ago`
  if (h > 0) return `${h}h ago`
  if (m > 0) return `${m}m ago`
  return 'Just now'
}

export const fmtDuration = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}
