import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, X, FileCode, Zap, AlertCircle } from 'lucide-react'
import { reviewsApi } from '../utils/api'
import { langIcon } from '../utils/store'
import { Spinner } from '../components/UI'
import clsx from 'clsx'

const ACCEPTED = {
  'text/plain': ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.cc', '.c', '.h', '.go', '.rs'],
  'application/octet-stream': ['.py', '.js', '.ts', '.java', '.go', '.rs'],
}

const EXT_LANG: Record<string, string> = {
  py: 'python', js: 'javascript', jsx: 'javascript',
  ts: 'typescript', tsx: 'typescript', java: 'java',
  cpp: 'cpp', cc: 'cpp', c: 'c', h: 'c', go: 'go', rs: 'rust',
}

function getLang(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  return EXT_LANG[ext] || 'unknown'
}

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([])
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressMsg, setProgressMsg] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const onDrop = useCallback((accepted: File[]) => {
    setFiles(prev => {
      const names = new Set(prev.map(f => f.name))
      const newFiles = accepted.filter(f => !names.has(f.name))
      return [...prev, ...newFiles].slice(0, 20)
    })
    if (!title && accepted.length > 0) {
      setTitle(accepted[0].name.replace(/\.[^.]+$/, '') + ' — Code Review')
    }
  }, [title])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: ACCEPTED, maxSize: 512 * 1024,
  })

  const removeFile = (name: string) => setFiles(prev => prev.filter(f => f.name !== name))

  const handleSubmit = async () => {
    if (!files.length) return
    if (!title.trim()) { setError('Please enter a review title'); return }
    setLoading(true)
    setError('')

    // Simulate WebSocket progress (real WS connection for live updates)
    const steps = [
      [15, 'Parsing source files...'],
      [30, 'Running security scan...'],
      [50, 'Computing complexity metrics...'],
      [65, 'Checking style conventions...'],
      [80, 'Detecting duplication...'],
      [92, 'Generating AI insights...'],
      [98, 'Finalizing report...'],
    ]
    let stepIdx = 0
    const interval = setInterval(() => {
      if (stepIdx < steps.length) {
        const [pct, msg] = steps[stepIdx]
        setProgress(pct as number)
        setProgressMsg(msg as string)
        stepIdx++
      }
    }, 400)

    try {
      const res = await reviewsApi.create(title.trim(), files)
      clearInterval(interval)
      setProgress(100)
      setProgressMsg('Analysis complete!')
      await new Promise(r => setTimeout(r, 400))
      navigate(`/reviews/${res.data.id}`)
    } catch (e: any) {
      clearInterval(interval)
      setLoading(false)
      setProgress(0)
      setError(e?.response?.data?.detail || 'Analysis failed. Please try again.')
    }
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="font-display font-bold text-2xl mb-1" style={{ color: 'var(--text-1)' }}>
          New Code Review
        </h1>
        <p className="text-sm" style={{ color: 'var(--text-2)' }}>
          Upload source files to receive instant AI-powered analysis with security scanning, complexity metrics, and fix suggestions.
        </p>
      </div>

      {/* Title input */}
      <div className="mb-5">
        <label className="block text-xs font-semibold mb-2 uppercase tracking-wider" style={{ color: 'var(--text-2)' }}>
          Review Title
        </label>
        <input
          value={title} onChange={e => setTitle(e.target.value)}
          placeholder="e.g. auth-service.py — Security Review"
          className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all"
          style={{ background: 'var(--surface)', border: '1px solid var(--border-2)', color: 'var(--text-1)' }}
          onFocus={e => (e.target.style.borderColor = 'var(--brand)')}
          onBlur={e => (e.target.style.borderColor = 'var(--border-2)')}
        />
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={clsx(
          'rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition-all duration-200 mb-5',
          isDragActive ? 'border-brand bg-brand-dim scale-[1.01]' : 'hover:border-brand hover:bg-brand-dim'
        )}
        style={{
          borderColor: isDragActive ? 'var(--brand)' : 'var(--border-2)',
          background: isDragActive ? 'rgba(108,99,255,0.06)' : 'var(--surface)',
        }}
      >
        <input {...getInputProps()} />
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
          style={{ background: 'rgba(108,99,255,0.12)', border: '1px solid rgba(108,99,255,0.2)' }}
        >
          <Upload className="w-6 h-6" style={{ color: 'var(--brand)' }} />
        </div>
        <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-1)' }}>
          {isDragActive ? 'Drop files here' : 'Drag & drop source files'}
        </p>
        <p className="text-xs" style={{ color: 'var(--text-3)' }}>
          or click to browse · Python, JS, TS, Java, Go, Rust, C/C++ · Max 500KB/file · Up to 20 files
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="rounded-xl overflow-hidden mb-6"
          style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}>
          <div className="px-4 py-3 border-b flex items-center justify-between"
            style={{ borderColor: 'var(--border)' }}>
            <span className="text-xs font-semibold" style={{ color: 'var(--text-2)' }}>
              {files.length} file{files.length !== 1 ? 's' : ''} queued
            </span>
            <button onClick={() => setFiles([])} className="text-xs hover:opacity-70 transition-opacity"
              style={{ color: 'var(--danger)' }}>
              Clear all
            </button>
          </div>
          {files.map(f => (
            <div key={f.name} className="flex items-center gap-3 px-4 py-3 border-b last:border-0"
              style={{ borderColor: 'var(--border)' }}>
              <span className="text-lg">{langIcon(getLang(f.name))}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate" style={{ color: 'var(--text-1)' }}>{f.name}</div>
                <div className="text-xs" style={{ color: 'var(--text-3)' }}>
                  {getLang(f.name)} · {(f.size / 1024).toFixed(1)} KB
                </div>
              </div>
              <button onClick={() => removeFile(f.name)}
                className="p-1 rounded hover:bg-white/10 transition-colors flex-shrink-0"
                style={{ color: 'var(--text-3)' }}>
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl mb-5 text-sm"
          style={{ background: 'rgba(255,77,109,0.08)', color: 'var(--danger)', border: '1px solid rgba(255,77,109,0.2)' }}>
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Progress */}
      {loading && (
        <div className="rounded-xl p-5 mb-5"
          style={{ background: 'var(--surface)', border: '1px solid rgba(108,99,255,0.2)' }}>
          <div className="flex items-center gap-3 mb-3">
            <Spinner size={16} />
            <span className="text-sm" style={{ color: 'var(--text-2)' }}>{progressMsg}</span>
            <span className="ml-auto text-xs font-mono" style={{ color: 'var(--brand)' }}>{progress}%</span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--surface-3)' }}>
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{ width: `${progress}%`, background: 'linear-gradient(90deg, var(--brand), #a78bfa)' }}
            />
          </div>
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={loading || files.length === 0}
        className="w-full py-3.5 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all"
        style={{
          background: files.length === 0 ? 'var(--surface-2)' : 'var(--brand)',
          color: files.length === 0 ? 'var(--text-3)' : 'white',
          boxShadow: files.length > 0 ? '0 0 24px rgba(108,99,255,0.3)' : 'none',
          opacity: loading ? 0.8 : 1,
          cursor: files.length === 0 || loading ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? (
          <><Spinner size={16} /><span>Analyzing...</span></>
        ) : (
          <><Zap className="w-4 h-4" /><span>Run AI Analysis</span></>
        )}
      </button>

      {/* Language support note */}
      <div className="mt-6 p-4 rounded-xl" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
        <p className="text-xs font-semibold mb-2" style={{ color: 'var(--text-3)' }}>WHAT WE DETECT</p>
        <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
          {[
            '🔒 Security vulnerabilities (12 rules)',
            '📊 Cyclomatic & cognitive complexity',
            '🐛 Mutable defaults, bare excepts',
            '⚡ Performance anti-patterns',
            '✏️ Style & naming conventions',
            '📄 Missing docstrings',
            '📋 Code duplication detection',
            '🔧 Maintainability Index (SEI formula)',
          ].map(item => (
            <div key={item} className="text-xs" style={{ color: 'var(--text-2)' }}>{item}</div>
          ))}
        </div>
      </div>
    </div>
  )
}
