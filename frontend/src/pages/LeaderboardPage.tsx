import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import { usersApi } from '../utils/api'
import { scoreColor } from '../utils/store'
import { ScoreRing, Spinner } from '../components/UI'
import { Trophy, Flame, Code2 } from 'lucide-react'
import { useStore } from '../utils/store'

export default function LeaderboardPage() {
  const { user: currentUser } = useStore()
  const { data, isLoading } = useQuery('leaderboard', () =>
    usersApi.leaderboard().then(r => r.data))

  const entries = data?.leaderboard || []

  const medalColor = (rank: number) => {
    if (rank === 1) return '#ffd700'
    if (rank === 2) return '#c0c0c0'
    if (rank === 3) return '#cd7f32'
    return 'var(--text-3)'
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: 'rgba(255,215,0,0.12)', border: '1px solid rgba(255,215,0,0.2)' }}>
          <Trophy className="w-5 h-5" style={{ color: '#ffd700' }} />
        </div>
        <div>
          <h1 className="font-display font-bold text-2xl" style={{ color: 'var(--text-1)' }}>
            Leaderboard
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-2)' }}>
            Top developers by code quality score
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20"><Spinner size={28} /></div>
      ) : (
        <div className="space-y-2">
          {entries.map((entry: any, i: number) => {
            const isMe = entry.username === currentUser?.username
            return (
              <Link
                key={entry.username}
                to={`/profile/${entry.username}`}
                className="flex items-center gap-4 p-4 rounded-xl transition-all animate-fade-up"
                style={{
                  background: isMe ? 'rgba(108,99,255,0.08)' : 'var(--surface)',
                  border: `1px solid ${isMe ? 'rgba(108,99,255,0.25)' : 'var(--border)'}`,
                  textDecoration: 'none',
                  animationDelay: `${i * 0.05}s`,
                }}
                onMouseEnter={e => !isMe && (e.currentTarget.style.borderColor = 'var(--border-2)')}
                onMouseLeave={e => !isMe && (e.currentTarget.style.borderColor = 'var(--border)')}
              >
                {/* Rank */}
                <div className="w-8 text-center flex-shrink-0">
                  {entry.rank <= 3 ? (
                    <span className="text-xl">
                      {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : '🥉'}
                    </span>
                  ) : (
                    <span className="text-sm font-bold" style={{ color: 'var(--text-3)' }}>
                      #{entry.rank}
                    </span>
                  )}
                </div>

                {/* Avatar */}
                <div className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0"
                  style={{
                    background: isMe ? 'rgba(108,99,255,0.2)' : 'var(--surface-2)',
                    color: isMe ? 'var(--brand)' : 'var(--text-2)',
                    border: `1px solid ${isMe ? 'rgba(108,99,255,0.3)' : 'var(--border-2)'}`,
                  }}>
                  {(entry.full_name || entry.username)[0].toUpperCase()}
                </div>

                {/* Name and stats */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm" style={{ color: 'var(--text-1)' }}>
                      {entry.full_name || entry.username}
                    </span>
                    {isMe && (
                      <span className="text-xs px-2 py-0.5 rounded font-medium"
                        style={{ background: 'rgba(108,99,255,0.15)', color: 'var(--brand)' }}>
                        You
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-3)' }}>
                      <Code2 className="w-3 h-3" />
                      {entry.total_reviews} reviews
                    </span>
                    {entry.streak_days > 0 && (
                      <span className="flex items-center gap-1 text-xs" style={{ color: '#ffb830' }}>
                        <Flame className="w-3 h-3" />
                        {entry.streak_days}d streak
                      </span>
                    )}
                  </div>
                </div>

                {/* Score */}
                <ScoreRing score={entry.quality_score || 0} size={44} strokeWidth={4} />
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
