import { useParams, Link } from 'react-router-dom'
import { useQuery } from 'react-query'
import { usersApi } from '../utils/api'
import { scoreColor, scoreLabel, timeAgo } from '../utils/store'
import { ScoreRing, Spinner, EmptyState } from '../components/UI'
import { Flame, Code2, Bug, Wrench, ChevronRight } from 'lucide-react'

export default function ProfilePage() {
  const { username } = useParams<{ username: string }>()

  const { data: profile, isLoading } = useQuery(
    ['profile', username],
    () => usersApi.profile(username!).then(r => r.data),
    { enabled: !!username }
  )

  if (isLoading) return (
    <div className="flex items-center justify-center h-screen"><Spinner size={28} /></div>
  )
  if (!profile) return (
    <div className="flex items-center justify-center h-screen">
      <EmptyState icon="👤" title="User not found" desc={`@${username} doesn't exist.`} />
    </div>
  )

  const score = profile.quality_score || 0

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Hero */}
      <div className="rounded-2xl p-8 mb-6 relative overflow-hidden"
        style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 50% 80% at 0% 50%, rgba(108,99,255,0.06), transparent)' }} />
        <div className="flex items-start gap-6">
          {/* Avatar */}
          <div className="w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-bold flex-shrink-0"
            style={{ background: 'rgba(108,99,255,0.15)', color: 'var(--brand)', border: '1px solid rgba(108,99,255,0.2)' }}>
            {(profile.full_name || profile.username)[0].toUpperCase()}
          </div>

          <div className="flex-1">
            <h1 className="font-display font-bold text-2xl mb-0.5" style={{ color: 'var(--text-1)' }}>
              {profile.full_name || profile.username}
            </h1>
            <p className="text-sm mb-3" style={{ color: 'var(--text-2)' }}>@{profile.username}</p>
            {profile.bio && (
              <p className="text-sm leading-relaxed mb-4" style={{ color: 'var(--text-2)' }}>{profile.bio}</p>
            )}
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <span className="flex items-center gap-1.5" style={{ color: 'var(--text-3)' }}>
                <Code2 className="w-4 h-4" />
                {profile.total_reviews} reviews
              </span>
              <span className="flex items-center gap-1.5" style={{ color: '#ffb830' }}>
                <Flame className="w-4 h-4" />
                {profile.streak_days}d streak
              </span>
              <span className="flex items-center gap-1.5" style={{ color: 'var(--text-3)' }}>
                <Bug className="w-4 h-4" />
                {profile.total_issues_found} issues found
              </span>
              <span className="flex items-center gap-1.5" style={{ color: 'var(--success)' }}>
                <Wrench className="w-4 h-4" />
                {profile.total_issues_fixed} fixed
              </span>
            </div>
          </div>

          {/* Score */}
          <div className="flex flex-col items-center gap-1">
            <ScoreRing score={score} size={90} strokeWidth={7} />
            <span className="text-xs" style={{ color: scoreColor(score) }}>{scoreLabel(score)}</span>
            <span className="text-xs" style={{ color: 'var(--text-3)' }}>Quality Score</span>
          </div>
        </div>

        <p className="text-xs mt-4" style={{ color: 'var(--text-3)' }}>
          Member since {profile.member_since ? new Date(profile.member_since).toLocaleDateString('en-IN', { year: 'numeric', month: 'long' }) : '—'}
        </p>
      </div>

      <div className="grid grid-cols-12 gap-5">
        {/* Badges */}
        <div className="col-span-12 md:col-span-5">
          <div className="rounded-xl p-5" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
            <h2 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-1)' }}>
              Badges ({profile.badges?.length || 0})
            </h2>
            {profile.badges?.length > 0 ? (
              <div className="grid grid-cols-3 gap-3">
                {profile.badges.map((b: any) => (
                  <div
                    key={b.slug}
                    title={b.name}
                    className="rounded-xl p-3 flex flex-col items-center gap-1.5 text-center cursor-help"
                    style={{ background: `${b.color}10`, border: `1px solid ${b.color}22` }}
                  >
                    <span className="text-2xl">{b.icon}</span>
                    <span className="text-xs font-medium leading-tight" style={{ color: b.color }}>
                      {b.name}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-center py-6" style={{ color: 'var(--text-3)' }}>
                No badges yet — complete reviews to earn them!
              </p>
            )}
          </div>
        </div>

        {/* Recent reviews */}
        <div className="col-span-12 md:col-span-7">
          <div className="rounded-xl p-5" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
            <h2 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-1)' }}>Recent Reviews</h2>
            {profile.recent_reviews?.length > 0 ? (
              <div className="space-y-2">
                {profile.recent_reviews.map((r: any) => (
                  <Link
                    key={r.id}
                    to={`/reviews/${r.id}`}
                    className="flex items-center gap-3 p-3 rounded-lg transition-all group"
                    style={{ border: '1px solid transparent' }}
                    onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--border-2)')}
                    onMouseLeave={e => (e.currentTarget.style.borderColor = 'transparent')}
                  >
                    {r.quality_score !== null && (
                      <ScoreRing score={r.quality_score} size={36} strokeWidth={3} showLabel={false} />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate" style={{ color: 'var(--text-1)' }}>{r.title}</div>
                      <div className="text-xs" style={{ color: 'var(--text-3)' }}>
                        {r.total_issues} issues · {timeAgo(r.created_at)}
                      </div>
                    </div>
                    {r.quality_score !== null && (
                      <span className="text-sm font-mono font-bold flex-shrink-0"
                        style={{ color: scoreColor(r.quality_score) }}>
                        {r.quality_score.toFixed(0)}
                      </span>
                    )}
                    <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity"
                      style={{ color: 'var(--brand)' }} />
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-center py-8" style={{ color: 'var(--text-3)' }}>
                No reviews yet
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
