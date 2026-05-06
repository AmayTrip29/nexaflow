import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts'
import { analyticsApi, reviewsApi } from '../utils/api'
import { useStore } from '../utils/store'
import { scoreColor, categoryIcon, timeAgo } from '../utils/store'
import { ScoreRing, StatCard, Spinner } from '../components/UI'
import { Upload, ChevronRight, ShieldAlert, Zap, BarChart3, Award } from 'lucide-react'

const TT = {
  contentStyle: { background: '#16162a', border: '1px solid #2a2a45', borderRadius: '8px', color: '#e8e8f5', fontSize: '12px' },
  labelStyle: { color: '#9090c0' },
}

const CAT_COLORS: Record<string, string> = {
  security: '#ff4d6d', complexity: '#a78bfa', style: '#38bdf8',
  performance: '#ffb830', maintainability: '#22d3a0', bug: '#ff7c00',
  documentation: '#6c63ff', duplication: '#9090c0',
}

export default function DashboardPage() {
  const { user } = useStore()
  const { data: analytics, isLoading } = useQuery('analytics-dash', () =>
    analyticsApi.dashboard().then(r => r.data), { refetchInterval: 60000 })
  const { data: reviewsData } = useQuery('reviews-dash', () =>
    reviewsApi.list({ limit: 5 }).then(r => r.data))

  if (isLoading) return (
    <div className="flex items-center justify-center h-screen">
      <Spinner size={32} />
    </div>
  )

  const dash = analytics || {}
  const trend = dash.quality_trend || []
  const bySeverity = dash.issues_by_severity || []
  const byCategory = dash.issues_by_category || []
  const badges = dash.badges || []
  const topRules = dash.top_rules || []
  const stats = dash.stats || {}
  const recentReviews = reviewsData?.reviews || []

  const qualityScore = dash.user?.quality_score || 0

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="font-display font-bold text-2xl mb-1" style={{ color: 'var(--text-1)' }}>
            Dashboard
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-2)' }}>
            Welcome back, {dash.user?.full_name?.split(' ')[0] || 'developer'}
          </p>
        </div>
        <Link
          to="/upload"
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all hover:opacity-90"
          style={{ background: 'var(--brand)', color: 'white', boxShadow: '0 0 20px rgba(108,99,255,0.25)' }}
        >
          <Upload className="w-4 h-4" />
          New Review
        </Link>
      </div>

      {/* Quality score hero */}
      <div
        className="rounded-2xl p-6 mb-6 flex items-center gap-8 relative overflow-hidden"
        style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 60% 80% at 5% 50%, rgba(108,99,255,0.07) 0%, transparent 70%)' }}
        />
        <ScoreRing score={qualityScore} size={100} strokeWidth={8} />
        <div className="flex-1">
          <div className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: 'var(--text-3)' }}>
            Your Quality Score
          </div>
          <div className="font-display font-bold text-3xl mb-1" style={{ color: scoreColor(qualityScore) }}>
            {qualityScore.toFixed(1)} / 100
          </div>
          <div className="text-sm" style={{ color: 'var(--text-2)' }}>
            Across {stats.total_reviews || 0} reviews · {stats.total_lines_reviewed?.toLocaleString() || 0} lines analyzed
          </div>
        </div>
        <div className="flex gap-2 flex-wrap">
          {badges.slice(0, 4).map((b: any) => (
            <div
              key={b.slug}
              title={b.description}
              className="w-10 h-10 rounded-xl flex items-center justify-center text-xl cursor-help transition-transform hover:scale-110"
              style={{ background: `${b.color}18`, border: `1px solid ${b.color}33` }}
            >
              {b.icon}
            </div>
          ))}
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Reviews" value={stats.total_reviews || 0}
          sub="Code reviews completed" color="var(--brand)"
          icon={<BarChart3 className="w-5 h-5" />} />
        <StatCard label="Issues Found" value={(dash.user?.total_issues_found || 0).toLocaleString()}
          sub="Across all reviews" color="#ff7c00"
          icon={<ShieldAlert className="w-5 h-5" />} />
        <StatCard label="Fixable Issues" value={stats.fixable_issues || 0}
          sub="Auto-fix available" color="var(--success)"
          icon={<Zap className="w-5 h-5" />} />
        <StatCard label="Streak" value={`${dash.user?.streak_days || 0}d`}
          sub="Consecutive review days" color="#ffb830"
          icon={<Award className="w-5 h-5" />} />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-12 gap-4 mb-6">
        {/* Quality trend */}
        <div className="col-span-12 lg:col-span-8 rounded-xl p-5"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-1)' }}>Quality Score Trend</h2>
          {trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={trend}>
                <defs>
                  <linearGradient id="qGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6c63ff" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6c63ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(42,42,69,0.8)" />
                <XAxis dataKey="review_num" tick={{ fill: '#6060a0', fontSize: 10 }} tickLine={false} axisLine={false} label={{ value: 'Review #', position: 'insideBottom', offset: -5, fill: '#6060a0', fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fill: '#6060a0', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip {...TT} formatter={(v: any) => [`${v}/100`, 'Quality']} />
                <Area type="monotone" dataKey="score" stroke="#6c63ff" strokeWidth={2} fill="url(#qGrad)" dot={{ fill: '#6c63ff', r: 3 }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-44 flex items-center justify-center text-sm" style={{ color: 'var(--text-3)' }}>
              Complete more reviews to see your trend
            </div>
          )}
        </div>

        {/* By severity */}
        <div className="col-span-12 lg:col-span-4 rounded-xl p-5"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-1)' }}>Issues by Severity</h2>
          <ResponsiveContainer width="100%" height={150}>
            <BarChart data={bySeverity} layout="vertical">
              <XAxis type="number" tick={{ fill: '#6060a0', fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="severity" tick={{ fill: '#9090c0', fontSize: 11 }} tickLine={false} axisLine={false} width={55} />
              <Tooltip {...TT} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]} name="Count">
                {bySeverity.map((entry: any) => (
                  <Cell key={entry.severity} fill={
                    entry.severity === 'critical' ? '#ff4d6d' :
                    entry.severity === 'error' ? '#ff7c00' :
                    entry.severity === 'warning' ? '#ffb830' : '#38bdf8'
                  } />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-12 gap-4">
        {/* Recent reviews */}
        <div className="col-span-12 lg:col-span-7 rounded-xl p-5"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold" style={{ color: 'var(--text-1)' }}>Recent Reviews</h2>
            <Link to="/reviews" className="text-xs flex items-center gap-1 hover:opacity-70 transition-opacity"
              style={{ color: 'var(--brand)' }}>
              All reviews <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-2">
            {recentReviews.slice(0, 5).map((r: any) => (
              <Link
                key={r.id} to={`/reviews/${r.id}`}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-white/5 transition-all group"
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
            {recentReviews.length === 0 && (
              <div className="text-center py-8">
                <p className="text-sm mb-3" style={{ color: 'var(--text-3)' }}>No reviews yet</p>
                <Link to="/upload" className="text-xs px-4 py-2 rounded-lg font-semibold transition-all"
                  style={{ background: 'rgba(108,99,255,0.15)', color: 'var(--brand)', border: '1px solid rgba(108,99,255,0.2)' }}>
                  Upload your first file
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Top recurring issues */}
        <div className="col-span-12 lg:col-span-5 rounded-xl p-5"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-1)' }}>
            Top Recurring Issues
          </h2>
          <div className="space-y-3">
            {topRules.slice(0, 5).map((rule: any, i: number) => (
              <div key={rule.rule_id} className="flex items-center gap-3">
                <span className="text-xs font-mono font-bold w-6 text-right flex-shrink-0"
                  style={{ color: 'var(--text-3)' }}>#{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium truncate" style={{ color: 'var(--text-1)' }}>{rule.title}</div>
                  <div className="text-xs font-mono" style={{ color: 'var(--text-3)' }}>{rule.rule_id}</div>
                </div>
                <span className="text-sm font-bold flex-shrink-0" style={{ color: 'var(--warn)' }}>
                  ×{rule.count}
                </span>
              </div>
            ))}
            {topRules.length === 0 && (
              <p className="text-sm text-center py-4" style={{ color: 'var(--text-3)' }}>
                No patterns yet
              </p>
            )}
          </div>

          {/* By category mini chart */}
          {byCategory.length > 0 && (
            <div className="mt-5 pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
              <h3 className="text-xs font-semibold mb-3" style={{ color: 'var(--text-3)' }}>BY CATEGORY</h3>
              <div className="space-y-2">
                {byCategory.slice(0, 5).map((c: any) => {
                  const total = byCategory.reduce((s: number, x: any) => s + x.count, 0)
                  const pct = total > 0 ? (c.count / total) * 100 : 0
                  return (
                    <div key={c.category} className="flex items-center gap-2">
                      <span className="text-sm w-5">{categoryIcon(c.category)}</span>
                      <span className="text-xs flex-1" style={{ color: 'var(--text-2)' }}>{c.category}</span>
                      <div className="w-20 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--surface-3)' }}>
                        <div className="h-full rounded-full"
                          style={{ width: `${pct}%`, background: CAT_COLORS[c.category] || '#6c63ff' }} />
                      </div>
                      <span className="text-xs w-6 text-right" style={{ color: 'var(--text-3)' }}>{c.count}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
