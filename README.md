# ⚡ NexaFlow — AI-Powered Code Review Platform

<div align="center">

**Instant static analysis · Security scanning · Smart fix suggestions · Developer leaderboard**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6?style=flat-square&logo=typescript)](https://typescriptlang.org)
[![Tests](https://img.shields.io/badge/Tests-30_passing-22d3a0?style=flat-square)](tests/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Deploy](https://img.shields.io/badge/Deploy-Render_Free-46e3b7?style=flat-square&logo=render)](render.yaml)

[Live Demo](#quick-start) · [API Docs](http://localhost:8000/api/docs) · [Architecture](#architecture)

</div>

---

## What is NexaFlow?

NexaFlow is a full-stack platform that performs deep automated code review across multiple programming languages — **without any paid APIs, LLMs, or external services**. Everything runs locally using Python's AST, regex pattern matching, and established software metrics.

Upload your code and get back:

| What | How |
|------|-----|
| **Security vulnerabilities** | 12 pattern-based detectors (eval, SQL injection, hardcoded secrets...) |
| **Complexity metrics** | Cyclomatic (McCabe), Cognitive, Halstead Volume, Maintainability Index |
| **Style issues** | Bare excepts, wildcard imports, boolean comparisons, naming violations |
| **Smart fix suggestions** | Concrete before/after code diffs for every fixable issue |
| **Quality score 0–100** | Weighted aggregate across all metric categories |
| **AI-style summary** | Human-readable analysis, praise, and top priority — rule-based, no LLM |

---

## Why This Exists

Modern code review tools (SonarQube, Codacy, DeepSource) either cost money, require cloud services, or are too heavy to self-host easily. NexaFlow is:

- **Fully offline** — no API keys, no external calls, no data sent anywhere
- **Production-grade architecture** — async FastAPI, SQLAlchemy 2.0, React 18 + TypeScript
- **Deploy-ready in 2 minutes** — single Docker command or free Render.com hosting
- **Extensible** — add new rules in `engine.py`, new languages by extending the pattern database

---

## Quick Start

### One command (Docker)
```bash
git clone https://github.com/yourusername/nexaflow.git
cd nexaflow
docker-compose up -d
```
→ Frontend: http://localhost  
→ API: http://localhost:8000  
→ API Docs: http://localhost:8000/api/docs

Login: `alex / alex123` or `demo / demo123`

### Local development
```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```
→ http://localhost:5173

### Deploy free on Render.com
```bash
# Push to GitHub, connect on render.com — it reads render.yaml automatically
git push origin main
```

---

## Screenshots

### Dashboard
Real-time quality score, trend charts, issue breakdown by severity and category, recurring rule analysis, recent reviews — all in a single view.

### Upload & Analysis
Drag-and-drop multiple files. Real-time progress bar (WebSocket). Supports Python (deep AST), JavaScript, TypeScript, Java, Go, Rust, C/C++.

### Review Detail
Per-issue expandable cards with severity badges, line numbers, code snippets, concrete fix suggestions with before/after diffs, and one-click acknowledgment. AI-generated summary at the top.

### Leaderboard & Profiles
Gamified quality scores, streak tracking, badge system, per-user analytics with quality trend over time.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     NexaFlow Platform                         │
├──────────────────────────────────────────────────────────────┤
│  React 18 + TypeScript Frontend                               │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌──────────────┐  │
│  │Dashboard │ │  Upload   │ │  Review   │ │  Leaderboard │  │
│  │ Recharts │ │ Dropzone  │ │  Detail   │ │  + Profile   │  │
│  └──────────┘ └───────────┘ └───────────┘ └──────────────┘  │
│  Zustand (state) · React Query (cache) · Axios · Tailwind    │
├──────────────────────────────────────────────────────────────┤
│  FastAPI Backend (Python 3.11, fully async)                   │
│  ┌─────────────────────┐  ┌──────────────────────────────┐   │
│  │    REST API (/api/) │  │   WebSocket (/ws/analysis/)  │   │
│  │  Auth · Reviews     │  │   Live progress streaming    │   │
│  │  Issues · Analytics │  │                              │   │
│  │  Users · Repos      │  │                              │   │
│  └─────────────────────┘  └──────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐    │
│  │               Code Analysis Engine                    │    │
│  │  PythonASTAnalyzer   · SecurityPatternScanner         │    │
│  │  ComplexityCalculator · MaintainabilityIndexer        │    │
│  │  DuplicationDetector  · AIStyleSummaryGenerator       │    │
│  │  ResourceOptimizer    · EvacuationPlanner             │    │
│  └──────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────┤
│  SQLAlchemy 2.0 (AsyncSession) → SQLite / PostgreSQL          │
│  User · Repository · Review · ReviewFile · Issue              │
│  Suggestion · Badge · UserBadge                               │
└──────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Tech | Why |
|-------|------|-----|
| API | FastAPI 0.111 (async) | Non-blocking, Pydantic validation, auto-docs |
| ORM | SQLAlchemy 2.0 async | Type-safe, supports PostgreSQL in prod |
| Auth | JWT (jose) + bcrypt | Stateless, industry standard |
| Analysis | Python AST + regex | No paid APIs, fully offline, deterministic |
| Metrics | radon + custom | Battle-tested complexity algorithms |
| Frontend | React 18 + TypeScript | Type safety, excellent ecosystem |
| State | Zustand + React Query | Minimal boilerplate, smart server caching |
| Charts | Recharts | React-native SVG charts |
| Styling | Tailwind CSS + custom CSS | Fast iteration, consistent system |
| Deploy | Docker + Nginx | One-command deployment |
| CI/CD | GitHub Actions | Automated test + build on every push |

---

## Analysis Engine — Technical Details

### Detected Issues

#### Security (12 rules, `SEC*`)
| Rule | Issue | Severity |
|------|-------|----------|
| SEC001 | `eval()` usage | Critical |
| SEC002 | `exec()` usage | Critical |
| SEC003 | `subprocess` with `shell=True` | Critical |
| SEC004 | `os.system()` | Error |
| SEC005 | Pickle deserialization | Error |
| SEC006 | MD5 hash | Warning |
| SEC007 | SHA-1 hash | Warning |
| SEC008 | Hardcoded password | Critical |
| SEC009 | Hardcoded secret | Critical |
| SEC010 | Hardcoded API key | Critical |
| SEC011 | SQL string formatting | Critical |
| SEC012 | Non-cryptographic random | Info |

#### Performance (6 rules, `PERF*`)
`range(len())`, string concat in loops, wildcard imports, `time.sleep(0)`, global variables

#### Style (7 rules, `STYLE*`)
Bare except, broad Exception, empty `pass`, `print()` statements, TODO comments, `== True/False`, `== None`

#### Maintainability (4 rules, `MAINT*`)
Too many parameters, nested lambdas, `# type: ignore`, `noqa` suppression

#### AST-level (Python-specific, `AST*`)
Function not snake_case, missing docstring, mutable default argument, function too long (>50 lines), too many arguments (>7), class not PascalCase, line too long (>120 chars)

#### Complexity (`COMP*`)
Cyclomatic complexity (thresholds: warn@7, error@10, critical@20), cognitive complexity (warn@15)

### Quality Score Formula
```
score = 100
  − (critical_issues × 15)
  − (error_issues × 8)
  − (warning_issues × 3)
  − (info_issues × 0.5)
  − complexity_penalty(0–15)
  + maintainability_bonus(±5–10)

clamped to [0, 100]
```

### Maintainability Index (SEI formula)
```
MI = 171 − 5.2·ln(HV) − 0.23·CC − 16.2·ln(LOC) + 50·sin(√(2.4·CM))
scaled to 0–100
```
Where: HV = Halstead Volume, CC = Cyclomatic Complexity, LOC = Lines of Code, CM = Comment Ratio

---

## API Reference

Full interactive docs at `/api/docs`

```
POST   /api/auth/login              JWT login
POST   /api/auth/register           Create account
GET    /api/auth/me                 Current user + badges

GET    /api/reviews/                List reviews (paginated)
POST   /api/reviews/                Create review (upload files)
GET    /api/reviews/{id}            Full review with files + issues
DELETE /api/reviews/{id}            Delete review

GET    /api/issues/review/{id}      Review issues (filterable: severity, category, fixable)
PATCH  /api/issues/{id}/acknowledge Toggle acknowledged state

GET    /api/analytics/dashboard     User analytics (trend, charts, badges)
GET    /api/analytics/global        Platform-wide stats (public)

GET    /api/users/leaderboard       Top 10 by quality score
GET    /api/users/{username}/profile Public profile

GET    /api/repos/                  User repositories
POST   /api/repos/                  Create repository

WS     /ws/analysis/{review_id}     Real-time progress stream
```

### Example — Create a Review

```bash
curl -X POST http://localhost:8000/api/reviews/ \
  -H "Authorization: Bearer <token>" \
  -F "title=auth module review" \
  -F "files=@auth.py"
```

Response includes quality score, all issues with fixes, AI summary, metrics.

---

## Running Tests

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

**30 tests** covering:
- Auth (login, register, JWT validation, unauthorized access)
- Reviews (CRUD, multi-file, status filtering)
- Issues (severity/category filtering, acknowledgment)
- Analytics (dashboard, global stats)
- Users (leaderboard ordering, profiles)
- Analyzer unit tests (eval detection, SQL injection, mutable defaults, syntax errors, quality scoring, Halstead, MI)

---

## Project Structure

```
nexaflow/
├── backend/
│   ├── app/
│   │   ├── analyzer/
│   │   │   └── engine.py         # 600-line analysis engine
│   │   ├── api/
│   │   │   └── routes.py         # All API routes + WebSocket
│   │   ├── core/
│   │   │   ├── config.py         # Settings
│   │   │   ├── database.py       # Async SQLAlchemy
│   │   │   ├── auth.py           # JWT utilities
│   │   │   └── seeder.py         # Demo data
│   │   ├── models/
│   │   │   └── models.py         # 8 SQLAlchemy models
│   │   └── main.py               # FastAPI app
│   ├── tests/
│   │   └── test_all.py           # 30 pytest-asyncio tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/                # 6 full pages
│       │   ├── LoginPage.tsx
│       │   ├── DashboardPage.tsx
│       │   ├── UploadPage.tsx
│       │   ├── ReviewsPage.tsx
│       │   ├── ReviewDetailPage.tsx
│       │   ├── LeaderboardPage.tsx
│       │   └── ProfilePage.tsx
│       ├── components/
│       │   ├── Layout.tsx        # Sidebar navigation
│       │   └── UI.tsx            # ScoreRing, SevBadge, StatCard...
│       ├── utils/
│       │   ├── api.ts            # Axios client + all API calls + types
│       │   └── store.ts          # Zustand store + helper functions
│       ├── App.tsx               # Router
│       └── index.css             # Design system
├── docker-compose.yml
├── render.yaml                   # Free Render.com deployment
├── .github/workflows/ci.yml
└── README.md
```

---

## Roadmap

- [x] Python deep AST analysis
- [x] 29 rules across 4 categories
- [x] SEI Maintainability Index
- [x] Duplication detection
- [x] Smart fix suggestions
- [x] WebSocket progress streaming
- [x] Gamification (badges, streaks, leaderboard)
- [x] Docker + free Render.com deployment
- [ ] JavaScript/TypeScript deep AST (currently regex-based)
- [ ] GitHub PR integration (webhook → auto-review)
- [ ] VS Code extension
- [ ] Diff-mode: review only changed lines
- [ ] Custom rule configuration per project
- [ ] Export report as PDF

---

## License

MIT — free to use, modify, and deploy.

---

<div align="center">
Built with Python + React · Zero paid APIs · 100% open source
</div>
