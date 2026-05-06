import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, FileCode2, Upload, Trophy, LogOut, Zap, ChevronRight } from 'lucide-react'
import { useStore } from '../utils/store'
import { scoreColor } from '../utils/store'
import clsx from 'clsx'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/reviews', icon: FileCode2, label: 'Reviews' },
  { to: '/upload', icon: Upload, label: 'New Review' },
  { to: '/leaderboard', icon: Trophy, label: 'Leaderboard' },
]

export default function Layout() {
  const { user, logout } = useStore()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg)' }}>
      {/* Sidebar */}
      <aside
        className="w-60 flex flex-col flex-shrink-0 border-r relative"
        style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
      >
        {/* Subtle top glow */}
        <div
          className="absolute top-0 left-0 right-0 h-px"
          style={{ background: 'linear-gradient(90deg, transparent, var(--brand), transparent)' }}
        />

        {/* Logo */}
        <div className="px-5 py-6 flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: 'var(--brand)', boxShadow: '0 0 20px #6c63ff44' }}
          >
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-700 text-lg tracking-tight" style={{ color: 'var(--text-1)' }}>
            Nexa<span style={{ color: 'var(--brand)' }}>Flow</span>
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'text-white'
                    : 'hover:bg-white/5'
                )
              }
              style={({ isActive }) => isActive
                ? { background: 'rgba(108,99,255,0.15)', color: 'var(--brand)', border: '1px solid rgba(108,99,255,0.2)' }
                : { color: 'var(--text-2)' }
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User section */}
        <div className="border-t p-3" style={{ borderColor: 'var(--border)' }}>
          {user && (
            <button
              onClick={() => navigate(`/profile/${user.username}`)}
              className="w-full flex items-center gap-3 p-2.5 rounded-lg hover:bg-white/5 transition-all text-left mb-2"
            >
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold"
                style={{ background: 'rgba(108,99,255,0.2)', color: 'var(--brand)' }}
              >
                {(user.full_name || user.username)[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold truncate" style={{ color: 'var(--text-1)' }}>
                  {user.full_name || user.username}
                </div>
                <div className="text-xs" style={{ color: scoreColor(user.quality_score || 0) }}>
                  Score: {(user.quality_score || 0).toFixed(0)}
                </div>
              </div>
              <ChevronRight className="w-3 h-3 flex-shrink-0" style={{ color: 'var(--text-3)' }} />
            </button>
          )}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all hover:bg-white/5"
            style={{ color: 'var(--text-2)' }}
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
