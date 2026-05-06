import { scoreColor, scoreLabel } from '../utils/store'

// ── Score Ring ────────────────────────────────────────────────────────────────
interface ScoreRingProps {
  score: number
  size?: number
  strokeWidth?: number
  showLabel?: boolean
}

export function ScoreRing({ score, size = 80, strokeWidth = 6, showLabel = true }: ScoreRingProps) {
  const r = (size - strokeWidth * 2) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = scoreColor(score)

  return (
    <div className="relative flex items-center justify-center flex-shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={color} strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)', filter: `drop-shadow(0 0 6px ${color}66)` }}
        />
      </svg>
      {showLabel && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display font-bold text-sm" style={{ color }}>{score.toFixed(0)}</span>
          {size > 60 && <span className="text-xs" style={{ color: 'var(--text-3)', fontSize: '9px' }}>/100</span>}
        </div>
      )}
    </div>
  )
}

// ── Severity Badge ─────────────────────────────────────────────────────────────
export function SevBadge({ severity }: { severity: string }) {
  const labels: Record<string, string> = {
    critical: 'Critical', error: 'Error', warning: 'Warning', info: 'Info'
  }
  return (
    <span className={`sev-${severity} text-xs font-semibold px-2 py-0.5 rounded`}>
      {labels[severity] || severity}
    </span>
  )
}

// ── Stat Card ──────────────────────────────────────────────────────────────────
interface StatCardProps {
  label: string
  value: string | number
  sub?: string
  color?: string
  icon?: React.ReactNode
}

export function StatCard({ label, value, sub, color = 'var(--brand)', icon }: StatCardProps) {
  return (
    <div
      className="rounded-xl p-5 flex flex-col gap-3 animate-fade-up"
      style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center justify-between">
        {icon && <div className="opacity-60">{icon}</div>}
        <div
          className="text-3xl font-display font-bold"
          style={{ color }}
        >
          {value}
        </div>
      </div>
      <div>
        <div className="text-sm font-medium" style={{ color: 'var(--text-1)' }}>{label}</div>
        {sub && <div className="text-xs mt-0.5" style={{ color: 'var(--text-3)' }}>{sub}</div>}
      </div>
    </div>
  )
}

// ── Empty State ────────────────────────────────────────────────────────────────
export function EmptyState({ icon, title, desc, action }: {
  icon: React.ReactNode; title: string; desc: string; action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="text-5xl mb-4 opacity-30">{icon}</div>
      <div className="font-semibold mb-2" style={{ color: 'var(--text-1)' }}>{title}</div>
      <div className="text-sm mb-6" style={{ color: 'var(--text-3)' }}>{desc}</div>
      {action}
    </div>
  )
}

// ── Loading Spinner ────────────────────────────────────────────────────────────
export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <div
      className="rounded-full border-2 animate-spin flex-shrink-0"
      style={{
        width: size, height: size,
        borderColor: 'var(--border-2)',
        borderTopColor: 'var(--brand)',
      }}
    />
  )
}

// ── Progress Bar ───────────────────────────────────────────────────────────────
export function ProgressBar({ value, color, label }: { value: number; color?: string; label?: string }) {
  return (
    <div>
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-xs" style={{ color: 'var(--text-2)' }}>{label}</span>
          <span className="text-xs font-mono" style={{ color: color || 'var(--brand)' }}>{value.toFixed(0)}%</span>
        </div>
      )}
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--surface-3)' }}>
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${value}%`, background: color || 'var(--brand)', boxShadow: `0 0 8px ${color || 'var(--brand)'}66` }}
        />
      </div>
    </div>
  )
}
