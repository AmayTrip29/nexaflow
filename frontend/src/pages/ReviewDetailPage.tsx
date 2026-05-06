import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { reviewsApi, issuesApi } from '../utils/api'
import type { Issue, ReviewFile } from '../utils/api'
import {
  scoreColor, scoreLabel, severityColor, categoryIcon,
  langIcon, timeAgo, fmtDuration
} from '../utils/store'
import {
  ScoreRing, SevBadge, Spinner, ProgressBar, EmptyState
} from '../components/UI'
import {
  ArrowLeft, ChevronDown, ChevronUp, CheckCircle,
  Copy, Shield, Lightbulb, FileCode2, BarChart2,
  AlertTriangle, Info, Wrench
} from 'lucide-react'
import clsx from 'clsx'

// ── Issue Card ────────────────────────────────────────────────────────────────
function IssueCard({ issue, onAck }: { issue: Issue; onAck: (id: number) => void }) {
  const [expanded, setExpanded] = useState(false)
  const [copiedFix, setCopiedFix] = useState(false)

  const copyFix = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopiedFix(true)
    setTimeout(() => setCopiedFix(false), 2000)
  }

  return (
    <div
      className={clsx('rounded-xl overflow-hidden transition-all duration-200', issue.is_acknowledged && 'opacity-50')}
      style={{
        border: `1px solid ${severityColor(issue.severity)}28`,
        background: `${severityColor(issue.severity)}06`,
      }}
    >
      {/* Header */}
      <div
        className="flex items-start gap-3 p-4 cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <div
          className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0"
          style={{ background: severityColor(issue.severity) }}
        />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <SevBadge severity={issue.severity} />
            <span className="cat-tag">{categoryIcon(issue.category)} {issue.category}</span>
            <span className="text-xs font-mono" style={{ color: 'var(--text-3)' }}>
              {issue.rule_id}
            </span>
            {issue.line_start && (
              <span className="text-xs" style={{ color: 'var(--text-3)' }}>
                Line {issue.line_start}
              </span>
            )}
            {issue.is_fixable && (
              <span className="flex items-center gap-1 text-xs px-1.5 py-0.5 rounded"
                style={{ background: 'rgba(34,211,160,0.1)', color: 'var(--success)', border: '1px solid rgba(34,211,160,0.2)' }}>
                <Wrench className="w-2.5 h-2.5" /> Auto-fix
              </span>
            )}
          </div>
          <div className="text-sm font-medium" style={{ color: 'var(--text-1)' }}>
            {issue.title}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={e => { e.stopPropagation(); onAck(issue.id) }}
            title={issue.is_acknowledged ? 'Mark as unresolved' : 'Mark as resolved'}
            className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
            style={{ color: issue.is_acknowledged ? 'var(--success)' : 'var(--text-3)' }}
          >
            <CheckCircle className="w-4 h-4" />
          </button>
          {expanded ? <ChevronUp className="w-4 h-4" style={{ color: 'var(--text-3)' }} /> : <ChevronDown className="w-4 h-4" style={{ color: 'var(--text-3)' }} />}
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t px-4 pb-4 pt-4 space-y-4" style={{ borderColor: `${severityColor(issue.severity)}20` }}>
          {/* Message */}
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-2)' }}>
            {issue.message}
          </p>

          {/* Code snippet */}
          {issue.code_snippet && (
            <div>
              <p className="text-xs font-semibold mb-1.5 uppercase tracking-wider" style={{ color: 'var(--text-3)' }}>
                Found at line {issue.line_start}
              </p>
              <pre className="code-block p-3 text-xs diff-remove overflow-x-auto">
                <code style={{ color: '#ff4d6d' }}>{issue.code_snippet}</code>
              </pre>
            </div>
          )}

          {/* Fix suggestion */}
          {issue.fix_description && (
            <div className="rounded-lg p-3"
              style={{ background: 'rgba(34,211,160,0.06)', border: '1px solid rgba(34,211,160,0.15)' }}>
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="w-3.5 h-3.5" style={{ color: 'var(--success)' }} />
                <span className="text-xs font-semibold" style={{ color: 'var(--success)' }}>
                  Suggested Fix
                </span>
              </div>
              <pre className="text-xs leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--text-2)' }}>
                {issue.fix_description}
              </pre>
              {issue.fix_code_snippet && (
                <div className="mt-2 relative">
                  <pre className="code-block p-3 text-xs diff-add overflow-x-auto">
                    <code style={{ color: 'var(--success)' }}>{issue.fix_code_snippet}</code>
                  </pre>
                  <button
                    onClick={() => copyFix(issue.fix_code_snippet!)}
                    className="absolute top-2 right-2 p-1.5 rounded hover:bg-white/10 transition-colors"
                    style={{ color: copiedFix ? 'var(--success)' : 'var(--text-3)' }}
                  >
                    {copiedFix ? <CheckCircle className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* AI suggestions */}
          {issue.suggestions?.map(s => (
            <div key={s.id} className="rounded-lg p-4"
              style={{ background: 'rgba(108,99,255,0.06)', border: '1px solid rgba(108,99,255,0.15)' }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold" style={{ color: 'var(--brand)' }}>
                  💡 {s.title}
                </span>
                <span className="text-xs font-mono" style={{ color: 'var(--text-3)' }}>
                  {(s.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>
              <p className="text-xs leading-relaxed mb-3" style={{ color: 'var(--text-2)' }}>
                {s.explanation}
              </p>
              {(s.before_code || s.after_code) && (
                <div className="grid grid-cols-1 gap-2">
                  {s.before_code && (
                    <div>
                      <p className="text-xs mb-1" style={{ color: 'var(--danger)' }}>Before</p>
                      <pre className="code-block p-2.5 text-xs diff-remove overflow-x-auto">
                        <code style={{ color: '#ff4d6d' }}>{s.before_code}</code>
                      </pre>
                    </div>
                  )}
                  {s.after_code && (
                    <div>
                      <p className="text-xs mb-1" style={{ color: 'var(--success)' }}>After</p>
                      <pre className="code-block p-2.5 text-xs diff-add overflow-x-auto relative group">
                        <code style={{ color: 'var(--success)' }}>{s.after_code}</code>
                        <button
                          onClick={() => copyFix(s.after_code!)}
                          className="absolute top-2 right-2 p-1.5 rounded opacity-0 group-hover:opacity-100 hover:bg-white/10 transition-all"
                          style={{ color: 'var(--success)' }}
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── File Metrics Panel ────────────────────────────────────────────────────────
function FileMetricsPanel({ file }: { file: ReviewFile }) {
  const mi = file.maintainability_index || 0
  return (
    <div className="rounded-xl p-4 space-y-3"
      style={{ background: 'var(--surface-2)', border: '1px solid var(--border)' }}>
      <div className="flex items-center gap-2">
        <span className="text-lg">{langIcon(file.language)}</span>
        <span className="text-sm font-medium truncate" style={{ color: 'var(--text-1)' }}>{file.filename}</span>
        {file.quality_score !== null && (
          <span className="ml-auto text-xs font-mono font-bold"
            style={{ color: scoreColor(file.quality_score) }}>
            {file.quality_score.toFixed(0)}/100
          </span>
        )}
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        {[
          { label: 'LOC', value: file.lines_of_code },
          { label: 'Issues', value: file.issue_count },
          { label: 'Complexity', value: file.cyclomatic_complexity?.toFixed(1) ?? '—' },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-lg p-2"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div className="text-sm font-bold" style={{ color: 'var(--text-1)' }}>{value}</div>
            <div className="text-xs" style={{ color: 'var(--text-3)' }}>{label}</div>
          </div>
        ))}
      </div>
      <ProgressBar value={mi} color={scoreColor(mi)} label="Maintainability Index" />
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ReviewDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [selectedFile, setSelectedFile] = useState<number | null>(null)
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [fixableOnly, setFixableOnly] = useState(false)
  const [activeTab, setActiveTab] = useState<'issues' | 'metrics' | 'ai'>('issues')

  const { data: review, isLoading } = useQuery(
    ['review', id],
    () => reviewsApi.get(Number(id)).then(r => r.data),
    { refetchInterval: (data: any) => data?.status === 'analyzing' ? 3000 : false }
  )

  const { data: issuesData } = useQuery(
    ['issues', id, severityFilter, fixableOnly, selectedFile],
    () => issuesApi.byReview(Number(id), {
      severity: severityFilter !== 'all' ? severityFilter : undefined,
      fixable_only: fixableOnly || undefined,
    }).then(r => r.data),
    { enabled: !!review && review.status === 'complete' }
  )

  const ackMutation = useMutation(
    (issueId: number) => issuesApi.acknowledge(issueId),
    { onSuccess: () => qc.invalidateQueries(['issues', id]) }
  )

  if (isLoading) return (
    <div className="flex items-center justify-center h-screen"><Spinner size={28} /></div>
  )
  if (!review) return (
    <div className="flex items-center justify-center h-screen">
      <EmptyState icon="🔍" title="Review not found" desc="This review may have been deleted." />
    </div>
  )

  const allIssues = issuesData?.issues || []
  const files = review.files || []
  const displayIssues = selectedFile
    ? allIssues.filter((i: Issue) => files.find((f: ReviewFile) => f.id === selectedFile)?.issues.some((fi: Issue) => fi.id === i.id))
    : allIssues

  const score = review.quality_score ?? 0
  const isAnalyzing = review.status === 'analyzing' || review.status === 'pending'

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      {/* Top bar */}
      <div className="sticky top-0 z-20 border-b px-6 py-3 flex items-center gap-4"
        style={{ background: 'rgba(9,9,15,0.92)', borderColor: 'var(--border)', backdropFilter: 'blur(12px)' }}>
        <Link to="/reviews" className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          style={{ color: 'var(--text-2)' }}>
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="font-semibold text-sm truncate" style={{ color: 'var(--text-1)' }}>
            {review.title}
          </h1>
          <div className="text-xs flex items-center gap-2" style={{ color: 'var(--text-3)' }}>
            {review.total_files} file{review.total_files !== 1 ? 's' : ''} ·
            {(review.total_lines || 0).toLocaleString()} lines ·
            {timeAgo(review.created_at)}
            {review.analysis_duration_ms && <> · {fmtDuration(review.analysis_duration_ms)}</>}
          </div>
        </div>
        {isAnalyzing && (
          <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--brand)' }}>
            <Spinner size={14} />
            Analyzing...
          </div>
        )}
        {review.status === 'complete' && (
          <div className="flex items-center gap-2">
            <ScoreRing score={score} size={40} strokeWidth={4} />
            <div>
              <div className="text-sm font-bold" style={{ color: scoreColor(score) }}>
                {score.toFixed(0)}/100
              </div>
              <div className="text-xs" style={{ color: 'var(--text-3)' }}>{scoreLabel(score)}</div>
            </div>
          </div>
        )}
      </div>

      <div className="flex h-[calc(100vh-57px)]">
        {/* Left sidebar — file list */}
        {files.length > 1 && (
          <aside className="w-56 flex-shrink-0 border-r overflow-y-auto p-3 space-y-1"
            style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
            <p className="text-xs font-semibold px-2 py-1 uppercase tracking-wider" style={{ color: 'var(--text-3)' }}>
              Files
            </p>
            <button
              onClick={() => setSelectedFile(null)}
              className={clsx('w-full text-left px-3 py-2 rounded-lg text-xs transition-all',
                !selectedFile ? 'font-semibold' : 'hover:bg-white/5')}
              style={{
                background: !selectedFile ? 'rgba(108,99,255,0.12)' : 'transparent',
                color: !selectedFile ? 'var(--brand)' : 'var(--text-2)',
              }}
            >
              All files ({files.length})
            </button>
            {files.map((f: ReviewFile) => (
              <button
                key={f.id}
                onClick={() => setSelectedFile(selectedFile === f.id ? null : f.id)}
                className={clsx('w-full text-left px-3 py-2 rounded-lg transition-all',
                  selectedFile === f.id ? 'font-semibold' : 'hover:bg-white/5')}
                style={{
                  background: selectedFile === f.id ? 'rgba(108,99,255,0.12)' : 'transparent',
                  color: selectedFile === f.id ? 'var(--brand)' : 'var(--text-2)',
                }}
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-sm">{langIcon(f.language)}</span>
                  <span className="text-xs truncate">{f.filename}</span>
                </div>
                <div className="flex items-center justify-between mt-0.5">
                  <span className="text-xs" style={{ color: 'var(--text-3)' }}>
                    {f.issue_count} issues
                  </span>
                  {f.quality_score !== null && (
                    <span className="text-xs font-mono" style={{ color: scoreColor(f.quality_score) }}>
                      {f.quality_score.toFixed(0)}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </aside>
        )}

        {/* Main content */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 max-w-4xl">
            {isAnalyzing ? (
              <div className="flex flex-col items-center justify-center py-24 gap-4">
                <Spinner size={32} />
                <p className="text-sm" style={{ color: 'var(--text-2)' }}>Analysis in progress...</p>
              </div>
            ) : review.status === 'failed' ? (
              <div className="flex flex-col items-center justify-center py-24">
                <EmptyState icon="❌" title="Analysis failed"
                  desc="An error occurred during analysis. Please try again." />
              </div>
            ) : (
              <>
                {/* AI Summary */}
                {review.ai_summary && (
                  <div className="rounded-xl p-5 mb-6"
                    style={{ background: 'rgba(108,99,255,0.06)', border: '1px solid rgba(108,99,255,0.15)' }}>
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                        style={{ background: 'rgba(108,99,255,0.15)' }}>
                        <Lightbulb className="w-4 h-4" style={{ color: 'var(--brand)' }} />
                      </div>
                      <div className="flex-1 space-y-2">
                        <p className="text-sm leading-relaxed" style={{ color: 'var(--text-1)' }}>
                          {review.ai_summary}
                        </p>
                        {review.ai_praise && (
                          <div className="flex items-start gap-2">
                            <span className="text-xs mt-0.5">✅</span>
                            <p className="text-xs leading-relaxed" style={{ color: 'var(--success)' }}>
                              {review.ai_praise}
                            </p>
                          </div>
                        )}
                        {review.ai_top_priority && (
                          <div className="flex items-start gap-2">
                            <span className="text-xs mt-0.5">🎯</span>
                            <p className="text-xs leading-relaxed" style={{ color: 'var(--warn)' }}>
                              {review.ai_top_priority}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Issue count summary */}
                <div className="grid grid-cols-4 gap-3 mb-6">
                  {[
                    { label: 'Critical', count: review.critical_issues, color: '#ff4d6d', icon: <AlertTriangle className="w-4 h-4" /> },
                    { label: 'Error', count: review.error_issues, color: '#ff7c00', icon: <Shield className="w-4 h-4" /> },
                    { label: 'Warning', count: review.warning_issues, color: '#ffb830', icon: <Info className="w-4 h-4" /> },
                    { label: 'Info', count: review.info_issues, color: '#38bdf8', icon: <Info className="w-4 h-4" /> },
                  ].map(({ label, count, color, icon }) => (
                    <button
                      key={label}
                      onClick={() => setSeverityFilter(severityFilter === label.toLowerCase() ? 'all' : label.toLowerCase())}
                      className="rounded-xl p-3 text-center transition-all"
                      style={{
                        background: severityFilter === label.toLowerCase() ? `${color}18` : 'var(--surface)',
                        border: `1px solid ${severityFilter === label.toLowerCase() ? color + '44' : 'var(--border)'}`,
                      }}
                    >
                      <div className="flex items-center justify-center mb-1" style={{ color }}>{icon}</div>
                      <div className="text-xl font-display font-bold" style={{ color }}>{count}</div>
                      <div className="text-xs" style={{ color: 'var(--text-3)' }}>{label}</div>
                    </button>
                  ))}
                </div>

                {/* Metrics row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                  {[
                    { label: 'Maintainability', value: `${(review.maintainability_index || 0).toFixed(0)}/100`, color: scoreColor(review.maintainability_index || 0) },
                    { label: 'Avg Complexity', value: (review.avg_complexity || 0).toFixed(1), color: (review.avg_complexity || 0) > 10 ? '#ff7c00' : (review.avg_complexity || 0) > 7 ? '#ffb830' : 'var(--success)' },
                    { label: 'Duplication', value: `${(review.duplication_pct || 0).toFixed(1)}%`, color: (review.duplication_pct || 0) > 15 ? '#ff4d6d' : (review.duplication_pct || 0) > 5 ? '#ffb830' : 'var(--success)' },
                    { label: 'Total Issues', value: review.total_issues, color: 'var(--text-1)' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="rounded-xl p-4 text-center"
                      style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                      <div className="text-xl font-display font-bold" style={{ color }}>{value}</div>
                      <div className="text-xs mt-0.5" style={{ color: 'var(--text-3)' }}>{label}</div>
                    </div>
                  ))}
                </div>

                {/* File metrics (when multiple files) */}
                {files.length > 0 && (
                  <div className="mb-6">
                    <div className="flex items-center gap-2 mb-3">
                      <FileCode2 className="w-4 h-4" style={{ color: 'var(--text-3)' }} />
                      <h2 className="text-sm font-semibold" style={{ color: 'var(--text-1)' }}>File Analysis</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {(selectedFile
                        ? files.filter((f: ReviewFile) => f.id === selectedFile)
                        : files
                      ).map((f: ReviewFile) => (
                        <FileMetricsPanel key={f.id} file={f} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Filters */}
                <div className="flex items-center gap-3 mb-4">
                  <h2 className="text-sm font-semibold flex-1" style={{ color: 'var(--text-1)' }}>
                    Issues
                    {displayIssues.length > 0 && (
                      <span className="ml-2 text-xs font-normal" style={{ color: 'var(--text-3)' }}>
                        {displayIssues.length} shown
                      </span>
                    )}
                  </h2>
                  <label className="flex items-center gap-2 text-xs cursor-pointer"
                    style={{ color: 'var(--text-2)' }}>
                    <input
                      type="checkbox" checked={fixableOnly}
                      onChange={e => setFixableOnly(e.target.checked)}
                      className="accent-brand"
                    />
                    Fixable only
                  </label>
                  {severityFilter !== 'all' && (
                    <button onClick={() => setSeverityFilter('all')}
                      className="text-xs px-2 py-1 rounded"
                      style={{ background: 'var(--surface-2)', color: 'var(--text-2)' }}>
                      Clear filter
                    </button>
                  )}
                </div>

                {/* Issues list */}
                <div className="space-y-2">
                  {displayIssues.map((issue: Issue) => (
                    <IssueCard
                      key={issue.id}
                      issue={issue}
                      onAck={(id) => ackMutation.mutate(id)}
                    />
                  ))}
                  {displayIssues.length === 0 && review.total_issues === 0 && (
                    <div className="text-center py-12">
                      <div className="text-4xl mb-3">🎉</div>
                      <p className="text-sm font-medium mb-1" style={{ color: 'var(--success)' }}>
                        No issues found!
                      </p>
                      <p className="text-xs" style={{ color: 'var(--text-3)' }}>
                        Your code passed all checks.
                      </p>
                    </div>
                  )}
                  {displayIssues.length === 0 && review.total_issues > 0 && (
                    <div className="text-center py-8">
                      <p className="text-sm" style={{ color: 'var(--text-3)' }}>
                        No issues match the current filter.
                      </p>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
