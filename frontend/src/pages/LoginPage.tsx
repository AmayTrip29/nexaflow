import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap, Eye, EyeOff, ArrowRight } from 'lucide-react'
import { authApi } from '../utils/api'
import { useStore } from '../utils/store'

export default function LoginPage() {
  const [username, setUsername] = useState('demo')
  const [password, setPassword] = useState('demo123')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { setUser } = useStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await authApi.login(username, password)
      setUser(res.data.user, res.data.access_token)
      navigate('/dashboard')
    } catch {
      setError('Invalid credentials. Try demo / demo123')
    } finally {
      setLoading(false)
    }
  }

  const inp = "w-full px-4 py-3 rounded-lg text-sm outline-none transition-all duration-200"
  const inpStyle = {
    background: 'var(--surface-2)',
    border: '1px solid var(--border-2)',
    color: 'var(--text-1)',
  }

  return (
    <div
      className="min-h-screen flex dot-grid"
      style={{ background: 'var(--bg)' }}
    >
      {/* Left — branding */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-16"
        style={{ background: 'var(--surface)', borderRight: '1px solid var(--border)' }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--brand)' }}>
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="font-display font-bold text-xl" style={{ color: 'var(--text-1)' }}>
            Nexa<span style={{ color: 'var(--brand)' }}>Flow</span>
          </span>
        </div>

        <div>
          <h1 className="font-display font-bold text-5xl leading-tight mb-6" style={{ color: 'var(--text-1)' }}>
            Code smarter.<br />
            <span className="gradient-text">Ship cleaner.</span>
          </h1>
          <p className="text-lg leading-relaxed mb-10" style={{ color: 'var(--text-2)' }}>
            AI-powered static analysis that catches security vulnerabilities,
            complexity issues, and bad patterns — before they reach production.
          </p>

          {/* Feature list */}
          {[
            { icon: '🔒', label: '12 security vulnerability detectors' },
            { icon: '📊', label: 'Cyclomatic & cognitive complexity scoring' },
            { icon: '🤖', label: 'Smart fix suggestions for every issue' },
            { icon: '🏆', label: 'Gamified quality score & developer leaderboard' },
          ].map(({ icon, label }) => (
            <div key={label} className="flex items-center gap-3 mb-4">
              <span className="text-lg">{icon}</span>
              <span className="text-sm" style={{ color: 'var(--text-2)' }}>{label}</span>
            </div>
          ))}
        </div>

        <div className="text-xs" style={{ color: 'var(--text-3)' }}>
          © 2024 NexaFlow — Zero paid APIs. Fully open source.
        </div>
      </div>

      {/* Right — login form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 mb-10">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: 'var(--brand)' }}>
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-display font-bold text-lg" style={{ color: 'var(--text-1)' }}>
              Nexa<span style={{ color: 'var(--brand)' }}>Flow</span>
            </span>
          </div>

          <h2 className="font-display font-bold text-2xl mb-1" style={{ color: 'var(--text-1)' }}>
            Welcome back
          </h2>
          <p className="text-sm mb-8" style={{ color: 'var(--text-2)' }}>
            Sign in to your account
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-2)' }}>
                Username
              </label>
              <input
                value={username} onChange={e => setUsername(e.target.value)}
                className={inp} style={inpStyle} required autoFocus
                onFocus={e => (e.target.style.borderColor = 'var(--brand)')}
                onBlur={e => (e.target.style.borderColor = 'var(--border-2)')}
              />
            </div>

            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-2)' }}>
                Password
              </label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password} onChange={e => setPassword(e.target.value)}
                  className={inp + ' pr-11'} style={inpStyle} required
                  onFocus={e => (e.target.style.borderColor = 'var(--brand)')}
                  onBlur={e => (e.target.style.borderColor = 'var(--border-2)')}
                />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 opacity-50 hover:opacity-100 transition-opacity"
                  style={{ color: 'var(--text-2)' }}>
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="text-sm px-4 py-3 rounded-lg"
                style={{ background: 'rgba(255,77,109,0.1)', color: 'var(--danger)', border: '1px solid rgba(255,77,109,0.2)' }}>
                {error}
              </div>
            )}

            <button
              type="submit" disabled={loading}
              className="w-full py-3 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 transition-all"
              style={{
                background: 'var(--brand)',
                color: 'white',
                boxShadow: '0 0 20px rgba(108,99,255,0.3)',
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? (
                <div className="w-4 h-4 border-2 rounded-full animate-spin"
                  style={{ borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} />
              ) : (
                <><span>Sign in</span><ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>

          {/* Demo accounts */}
          <div className="mt-8 p-4 rounded-xl" style={{ background: 'var(--surface-2)', border: '1px solid var(--border)' }}>
            <p className="text-xs font-semibold mb-3" style={{ color: 'var(--text-3)' }}>DEMO ACCOUNTS</p>
            {[
              { u: 'alex', p: 'alex123', role: 'Senior dev — 12 reviews, badges' },
              { u: 'demo', p: 'demo123', role: 'Fresh account — start here' },
            ].map(({ u, p, role }) => (
              <button
                key={u}
                onClick={() => { setUsername(u); setPassword(p) }}
                className="w-full flex items-center justify-between text-left py-2 hover:opacity-70 transition-opacity"
              >
                <span className="text-xs font-mono" style={{ color: 'var(--brand)' }}>{u} / {p}</span>
                <span className="text-xs" style={{ color: 'var(--text-3)' }}>{role}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
