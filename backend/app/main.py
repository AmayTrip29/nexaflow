"""
NexaFlow — AI-Powered Code Review Platform
Main FastAPI Application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import (
    auth_router, reviews_router, issues_router,
    users_router, analytics_router, repos_router, ws_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 NexaFlow starting up...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created")

    from app.core.seeder import seed_database
    await seed_database()
    logger.info("✅ Database seeded")

    yield

    logger.info("🛑 NexaFlow shutting down...")
    await engine.dispose()


app = FastAPI(
    title="NexaFlow API",
    description="""
## NexaFlow — AI-Powered Code Review & Developer Productivity Platform

Automated static analysis, complexity metrics, security scanning,
and intelligent fix suggestions — all free, no API keys required.

### Features
- **Multi-language support**: Python (deep AST), JS/TS, Java, C/C++, Go, Rust
- **Security scanning**: 12 pattern-based vulnerability detectors
- **Complexity metrics**: Cyclomatic, Cognitive, Halstead, Maintainability Index
- **Smart suggestions**: Rule-based fix generation for every fixable issue
- **Gamification**: Badges, streaks, quality scores, leaderboard
- **Real-time WebSocket**: Live analysis progress streaming
""",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Routes
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(reviews_router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(issues_router, prefix="/api/issues", tags=["Issues"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(repos_router, prefix="/api/repos", tags=["Repositories"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "NexaFlow",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/api/docs",
        "description": "AI-Powered Code Review Platform",
    }


@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "healthy", "service": "NexaFlow", "version": settings.APP_VERSION}
