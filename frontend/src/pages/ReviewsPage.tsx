import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import { reviewsApi } from '../utils/api'
import { scoreColor, timeAgo, langIcon } from '../utils/store'
import { ScoreRing, EmptyState, Spinner } from '../components/UI'
import { Upload, ChevronRight, FileCode2, Clock, AlertTriangle } from 'lucide-react'

function statusDot(status: string) {
  const map: Record<string, string> = {
    complete: '#22d3a0', analyzing: '#6c63ff', pending: '#ffb830', failed: '#ff4d6d',
  }
  return map[status] || '#9090c0'
}

export default function ReviewsPage() {
  const { data, isLoading } = useQuery('reviews-list',
    () => reviewsApi.list({ limit: 50 }).then(r => r.data),
    { refetchInterval: 10000 }
  )

  const reviews = data?.reviews || []

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display font-bold text-2xl mb-1" style={{ color: 'var(--text-1)' }}>
            Code Reviews
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-2)' }}>
            {data?.total || 0} reviews completed
          </p>
        </div>
        <Link to="/upload"
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all hover:opacity-90"
          style={{ background: 'var(--brand)', color: 'white' }}>
          <Upload className="w-4 h-4" />
          New Review
        </Link>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20"><Spinner size={28} /></div>
      ) : reviews.length === 0 ? (
        <EmptyState
          icon={<FileCode2 />}
          title="No reviews yet"
          desc="Upload your first source file to get instant AI-powered code analysis."
          action={
            <Link to="/upload" className="px-5 py-2.5 rounded-lg text-sm font-semibold"
              style={{ background: 'var(--brand)', color: 'white' }}>
              Upload Code
            </Link>
          }
        />
      ) : (
        <div className="space-y-2">
          {reviews.map((r: any, i: number) => (
            <Link
              key={r.id}
              to={`/reviews/${r.id}`}
              className="flex items-center gap-4 p-4 rounded-xl transition-all group animate-fade-up"
              style={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                textDecoration: 'none',
                animationDelay: `${i * 0.04}s`,
              }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--border-2)')}
              onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
            >
              {/* Score ring or status */}
              {r.status === 'complete' && r.quality_score !== null ? (
                <ScoreRing score={r.quality_score} size={44} strokeWidth={4} showLabel={false} />
              ) : (
                <div className="w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ background: 'var(--surface-2)', border: `2px solid ${statusDot(r.status)}` }}>
                  {r.status === 'analyzing' ? (
                    <Spinner size={14} />
                  ) : (
                    <Clock className="w-4 h-4" style={{ color: statusDot(r.status) }} />
                  )}
                </div>
              )}

              {/* Main info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-sm font-medium truncate" style={{ color: 'var(--text-1)' }}>
                    {r.title}
                  </span>
                  {r.status !== 'complete' && (
                    <span
                      className="text-xs px-2 py-0.5 rounded font-medium flex-shrink-0"
                      style={{ background: `${statusDot(r.status)}18`, color: statusDot(r.status) }}
                    >
                      {r.status}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--text-3)' }}>
                  <span>{r.total_files} file{r.total_files !== 1 ? 's' : ''}</span>
                  <span>·</span>
                  <span>{(r.total_lines || 0).toLocaleString()} lines</span>
                  <span>·</span>
                  <span>{timeAgo(r.created_at)}</span>
                  {r.analysis_duration_ms && (
                    <><span>·</span><span>{r.analysis_duration_ms}ms</span></>
                  )}
                </div>
              </div>

              {/* Issue counts */}
              {r.status === 'complete' && (
                <div className="hidden md:flex items-center gap-4 flex-shrink-0">
                  {r.critical_issues > 0 && (
                    <div className="text-center">
                      <div className="text-sm font-bold" style={{ color: '#ff4d6d' }}>{r.critical_issues}</div>
                      <div className="text-xs" style={{ color: 'var(--text-3)' }}>Critical</div>
                    </div>
                  )}
                  {r.error_issues > 0 && (
                    <div className="text-center">
                      <div className="text-sm font-bold" style={{ color: '#ff7c00' }}>{r.error_issues}</div>
                      <div className="text-xs" style={{ color: 'var(--text-3)' }}>Error</div>
                    </div>
                  )}
                  <div className="text-center">
                    <div className="text-sm font-bold" style={{ color: 'var(--text-2)' }}>{r.total_issues}</div>
                    <div className="text-xs" style={{ color: 'var(--text-3)' }}>Total</div>
                  </div>
                  {r.quality_score !== null && (
                    <div className="text-center min-w-[48px]">
                      <div className="text-sm font-bold font-mono"
                        style={{ color: scoreColor(r.quality_score) }}>
                        {r.quality_score.toFixed(0)}
                      </div>
                      <div className="text-xs" style={{ color: 'var(--text-3)' }}>Score</div>
                    </div>
                  )}
                </div>
              )}

              <ChevronRight className="w-4 h-4 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                style={{ color: 'var(--brand)' }} />
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
