"""
NexaFlow API Routes — All in one module for clarity.
Split into separate files for production.
"""

# ─── Auth Router ──────────────────────────────────────────────────────────────
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import json

from app.core.database import get_db
from app.core.auth import verify_password, hash_password, create_access_token, get_current_user
from app.models.models import (
    User, Repository, Review, ReviewFile, Issue, Suggestion,
    Badge, UserBadge, ReviewStatus, Language, IssueSeverity, IssueCategory
)
from app.analyzer.engine import CodeAnalyzer

auth_router = APIRouter()
reviews_router = APIRouter()
issues_router = APIRouter()
users_router = APIRouter()
analytics_router = APIRouter()
repos_router = APIRouter()
ws_router = APIRouter()

analyzer = CodeAnalyzer()


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


@auth_router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account disabled")

    user.last_login = datetime.utcnow()
    await db.commit()
    token = create_access_token({"sub": user.username})
    return {
        "access_token": token, "token_type": "bearer",
        "user": {
            "id": user.id, "username": user.username, "full_name": user.full_name,
            "email": user.email, "quality_score": user.quality_score,
            "total_reviews": user.total_reviews, "streak_days": user.streak_days,
        },
    }


@auth_router.post("/register", status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(User).where((User.username == data.username) | (User.email == data.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already taken")

    user = User(
        username=data.username, email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name, is_active=True, is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "username": user.username}}


@auth_router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    badges_result = await db.execute(
        select(UserBadge, Badge)
        .join(Badge)
        .where(UserBadge.user_id == current_user.id)
        .order_by(desc(UserBadge.earned_at))
    )
    user_badges = [
        {
            "slug": badge.slug, "name": badge.name, "icon": badge.icon,
            "description": badge.description, "color": badge.color,
            "earned_at": ub.earned_at.isoformat(),
        }
        for ub, badge in badges_result.all()
    ]

    return {
        "id": current_user.id, "username": current_user.username,
        "email": current_user.email, "full_name": current_user.full_name,
        "bio": current_user.bio, "avatar_url": current_user.avatar_url,
        "quality_score": current_user.quality_score,
        "total_reviews": current_user.total_reviews,
        "total_issues_found": current_user.total_issues_found,
        "total_issues_fixed": current_user.total_issues_fixed,
        "streak_days": current_user.streak_days,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "badges": user_badges,
    }


# ─────────────────────────────────────────────────────────────────────────────
# REVIEWS
# ─────────────────────────────────────────────────────────────────────────────

@reviews_router.get("/")
async def list_reviews(
    skip: int = 0, limit: int = 20,
    status: Optional[ReviewStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Review)
        .where(Review.author_id == current_user.id)
        .order_by(desc(Review.created_at))
    )
    if status:
        query = query.where(Review.status == status)

    count_q = select(func.count(Review.id)).where(Review.author_id == current_user.id)
    total = (await db.execute(count_q)).scalar()
    result = await db.execute(query.offset(skip).limit(limit))
    reviews = result.scalars().all()
    return {"total": total, "reviews": [_ser_review(r) for r in reviews]}


@reviews_router.post("/", status_code=201)
async def create_review(
    title: str,
    files: List[UploadFile] = File(...),
    repository_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload one or more source files for AI-powered code review.
    Supports Python, JavaScript, TypeScript, Java, C/C++, Go, Rust.
    """
    from app.core.config import settings

    if len(files) > settings.MAX_FILES_PER_REVIEW:
        raise HTTPException(400, f"Max {settings.MAX_FILES_PER_REVIEW} files per review")

    # Read all files
    file_contents: dict[str, str] = {}
    for upload in files:
        content_bytes = await upload.read()
        if len(content_bytes) > settings.MAX_FILE_SIZE_KB * 1024:
            raise HTTPException(400, f"File {upload.filename} exceeds {settings.MAX_FILE_SIZE_KB}KB limit")
        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(400, f"File {upload.filename} is not valid UTF-8 text")
        file_contents[upload.filename] = content

    # Create review record (pending)
    review = Review(
        author_id=current_user.id,
        repository_id=repository_id,
        title=title,
        status=ReviewStatus.ANALYZING,
        total_files=len(file_contents),
    )
    db.add(review)
    await db.flush()

    # Run analysis
    try:
        review.status = ReviewStatus.ANALYZING
        metrics = await analyzer.analyze(file_contents)

        # Persist file records and issues
        for filename, file_metrics in metrics.per_file.items():
            from app.models.models import Language as Lang
            from app.analyzer.engine import detect_language
            lang_str = detect_language(filename, file_contents[filename])
            try:
                lang = Lang(lang_str)
            except ValueError:
                lang = Lang.UNKNOWN

            rf = ReviewFile(
                review_id=review.id,
                filename=filename,
                language=lang,
                content=file_contents[filename],
                lines_of_code=file_metrics.lines_of_code,
                blank_lines=file_metrics.blank_lines,
                comment_lines=file_metrics.comment_lines,
                cyclomatic_complexity=file_metrics.cyclomatic_complexity,
                cognitive_complexity=file_metrics.cognitive_complexity,
                maintainability_index=file_metrics.maintainability_index,
                halstead_volume=file_metrics.halstead_volume,
                issue_count=len(file_metrics.issues),
                quality_score=file_metrics.quality_score,
                annotations=file_metrics.annotations,
            )
            db.add(rf)
            await db.flush()

            for issue in file_metrics.issues:
                db_issue = Issue(
                    review_id=review.id, file_id=rf.id,
                    severity=IssueSeverity(issue.severity),
                    category=IssueCategory(issue.category),
                    rule_id=issue.rule_id, title=issue.title,
                    message=issue.message, line_start=issue.line_start,
                    line_end=issue.line_end, column_start=issue.column_start,
                    code_snippet=issue.code_snippet,
                    is_fixable=issue.is_fixable,
                    fix_description=issue.fix_description,
                    fix_code_snippet=issue.fix_code_snippet,
                )
                db.add(db_issue)
                await db.flush()

                if issue.fix_code_snippet:
                    db.add(Suggestion(
                        issue_id=db_issue.id,
                        title=f"Auto-fix: {issue.title}",
                        explanation=issue.fix_description or "",
                        after_code=issue.fix_code_snippet,
                        confidence=0.90,
                    ))

        # Update review with results
        review.quality_score = metrics.quality_score
        review.maintainability_index = metrics.maintainability_index
        review.total_issues = metrics.total_issues
        review.critical_issues = metrics.critical_issues
        review.error_issues = metrics.error_issues
        review.warning_issues = metrics.warning_issues
        review.info_issues = metrics.info_issues
        review.total_lines = metrics.total_lines
        review.avg_complexity = metrics.avg_complexity
        review.duplication_pct = metrics.duplication_pct
        review.ai_summary = metrics.ai_summary
        review.ai_praise = metrics.ai_praise
        review.ai_top_priority = metrics.ai_top_priority
        review.analysis_duration_ms = metrics.analysis_duration_ms
        review.status = ReviewStatus.COMPLETE
        review.completed_at = datetime.utcnow()

        # Update user stats
        current_user.total_reviews += 1
        current_user.total_issues_found += metrics.total_issues
        # Rolling quality score
        n = current_user.total_reviews
        current_user.quality_score = round(
            (current_user.quality_score * (n - 1) + metrics.quality_score) / n, 1
        )

        # Award first-review badge
        if current_user.total_reviews == 1:
            badges_result = await db.execute(select(Badge).where(Badge.slug == "first-review"))
            first_badge = badges_result.scalar_one_or_none()
            if first_badge:
                existing_ub = await db.execute(
                    select(UserBadge).where(
                        UserBadge.user_id == current_user.id,
                        UserBadge.badge_id == first_badge.id
                    )
                )
                if not existing_ub.scalar_one_or_none():
                    db.add(UserBadge(user_id=current_user.id, badge_id=first_badge.id))

        await db.commit()
        await db.refresh(review)
        return _ser_review(review, detailed=True)

    except Exception as e:
        review.status = ReviewStatus.FAILED
        await db.commit()
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@reviews_router.get("/{review_id}")
async def get_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.files).selectinload(ReviewFile.issues).selectinload(Issue.suggestions),
        )
        .where(Review.id == review_id, Review.author_id == current_user.id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, "Review not found")
    return _ser_review(review, detailed=True)


@reviews_router.delete("/{review_id}", status_code=204)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.author_id == current_user.id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, "Review not found")
    await db.delete(review)
    await db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# ISSUES
# ─────────────────────────────────────────────────────────────────────────────

@issues_router.get("/review/{review_id}")
async def get_review_issues(
    review_id: int,
    severity: Optional[IssueSeverity] = None,
    category: Optional[IssueCategory] = None,
    fixable_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify ownership
    rev_result = await db.execute(
        select(Review).where(Review.id == review_id, Review.author_id == current_user.id)
    )
    if not rev_result.scalar_one_or_none():
        raise HTTPException(404, "Review not found")

    query = (
        select(Issue)
        .options(selectinload(Issue.suggestions))
        .where(Issue.review_id == review_id)
        .order_by(
            Issue.severity.desc(),
            Issue.line_start.asc().nullslast(),
        )
    )
    if severity:
        query = query.where(Issue.severity == severity)
    if category:
        query = query.where(Issue.category == category)
    if fixable_only:
        query = query.where(Issue.is_fixable == True)

    result = await db.execute(query)
    issues = result.scalars().all()
    return {"issues": [_ser_issue(i) for i in issues]}


@issues_router.patch("/{issue_id}/acknowledge")
async def acknowledge_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Issue)
        .join(Review)
        .where(Issue.id == issue_id, Review.author_id == current_user.id)
    )
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(404, "Issue not found")
    issue.is_acknowledged = not issue.is_acknowledged
    await db.commit()
    return {"is_acknowledged": issue.is_acknowledged}


# ─────────────────────────────────────────────────────────────────────────────
# USERS / PROFILE
# ─────────────────────────────────────────────────────────────────────────────

@users_router.get("/leaderboard")
async def get_leaderboard(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .where(User.is_active == True)
        .order_by(desc(User.quality_score))
        .limit(10)
    )
    users = result.scalars().all()
    return {
        "leaderboard": [
            {
                "rank": i + 1, "username": u.username, "full_name": u.full_name,
                "quality_score": u.quality_score, "total_reviews": u.total_reviews,
                "streak_days": u.streak_days, "total_issues_found": u.total_issues_found,
            }
            for i, u in enumerate(users)
        ]
    }


@users_router.get("/{username}/profile")
async def get_user_profile(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    badges_result = await db.execute(
        select(UserBadge, Badge).join(Badge).where(UserBadge.user_id == user.id)
    )
    badges = [{"slug": b.slug, "name": b.name, "icon": b.icon, "color": b.color}
              for _, b in badges_result.all()]

    reviews_result = await db.execute(
        select(Review)
        .where(Review.author_id == user.id, Review.status == ReviewStatus.COMPLETE)
        .order_by(desc(Review.created_at))
        .limit(5)
    )
    recent_reviews = [_ser_review(r) for r in reviews_result.scalars().all()]

    return {
        "username": user.username, "full_name": user.full_name, "bio": user.bio,
        "quality_score": user.quality_score, "total_reviews": user.total_reviews,
        "streak_days": user.streak_days, "total_issues_found": user.total_issues_found,
        "total_issues_fixed": user.total_issues_fixed,
        "member_since": user.created_at.isoformat() if user.created_at else None,
        "badges": badges, "recent_reviews": recent_reviews,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

@analytics_router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reviews_result = await db.execute(
        select(Review)
        .where(Review.author_id == current_user.id, Review.status == ReviewStatus.COMPLETE)
        .order_by(Review.created_at)
    )
    reviews = reviews_result.scalars().all()

    # Quality trend (last 10 reviews)
    quality_trend = [
        {"review_num": i + 1, "title": r.title[:30], "score": r.quality_score,
         "date": r.created_at.strftime("%b %d") if r.created_at else ""}
        for i, r in enumerate(reviews[-10:])
    ]

    # Issue distribution
    all_issues_q = await db.execute(
        select(Issue)
        .join(Review)
        .where(Review.author_id == current_user.id)
    )
    all_issues = all_issues_q.scalars().all()

    by_category = {}
    by_severity = {"critical": 0, "error": 0, "warning": 0, "info": 0}
    for issue in all_issues:
        cat = issue.category.value if hasattr(issue.category, 'value') else str(issue.category)
        by_category[cat] = by_category.get(cat, 0) + 1
        sev = issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity)
        by_severity[sev] = by_severity.get(sev, 0) + 1

    # Most common issues
    rule_counts: dict[str, dict] = {}
    for issue in all_issues:
        rid = issue.rule_id
        if rid not in rule_counts:
            rule_counts[rid] = {"rule_id": rid, "title": issue.title, "count": 0, "severity": issue.severity}
        rule_counts[rid]["count"] += 1
    top_issues = sorted(rule_counts.values(), key=lambda x: x["count"], reverse=True)[:5]

    badges_result = await db.execute(
        select(UserBadge, Badge).join(Badge).where(UserBadge.user_id == current_user.id)
    )
    badges = [{"slug": b.slug, "name": b.name, "icon": b.icon, "description": b.description,
                "color": b.color, "earned_at": ub.earned_at.isoformat()}
              for ub, b in badges_result.all()]

    return {
        "user": {
            "username": current_user.username, "full_name": current_user.full_name,
            "quality_score": current_user.quality_score, "total_reviews": current_user.total_reviews,
            "streak_days": current_user.streak_days, "total_issues_found": current_user.total_issues_found,
        },
        "quality_trend": quality_trend,
        "issues_by_category": [{"category": k, "count": v} for k, v in by_category.items()],
        "issues_by_severity": [{"severity": k, "count": v} for k, v in by_severity.items()],
        "top_rules": top_issues,
        "badges": badges,
        "stats": {
            "avg_quality": round(sum(r.quality_score or 0 for r in reviews) / max(len(reviews), 1), 1),
            "total_lines_reviewed": sum(r.total_lines or 0 for r in reviews),
            "fixable_issues": sum(1 for i in all_issues if i.is_fixable),
            "total_reviews": len(reviews),
        },
    }


@analytics_router.get("/global")
async def get_global_analytics(db: AsyncSession = Depends(get_db)):
    """Platform-wide statistics — no auth required (public)."""
    users_count = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar()
    reviews_count = (await db.execute(select(func.count(Review.id)).where(Review.status == ReviewStatus.COMPLETE))).scalar()
    issues_count = (await db.execute(select(func.count(Issue.id)))).scalar()

    return {
        "total_users": users_count,
        "total_reviews": reviews_count,
        "total_issues_found": issues_count,
        "platform": "NexaFlow", "version": "1.0.0",
    }


# ─────────────────────────────────────────────────────────────────────────────
# REPOSITORIES
# ─────────────────────────────────────────────────────────────────────────────

@repos_router.get("/")
async def list_repos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Repository)
        .where(Repository.owner_id == current_user.id)
        .order_by(desc(Repository.updated_at))
    )
    repos = result.scalars().all()
    return {"repositories": [
        {"id": r.id, "name": r.name, "description": r.description,
         "language": r.language, "total_reviews": r.total_reviews,
         "avg_quality_score": r.avg_quality_score, "total_issues": r.total_issues}
        for r in repos
    ]}


class RepoCreate(BaseModel):
    name: str
    description: Optional[str] = None
    language: str = "python"
    is_public: bool = True


@repos_router.post("/", status_code=201)
async def create_repo(
    data: RepoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        lang = Language(data.language)
    except ValueError:
        lang = Language.UNKNOWN
    repo = Repository(
        owner_id=current_user.id, name=data.name,
        description=data.description, language=lang, is_public=data.is_public,
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    return {"id": repo.id, "name": repo.name, "message": "Repository created"}


# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import WebSocket, WebSocketDisconnect
import asyncio


@ws_router.websocket("/analysis/{review_id}")
async def analysis_progress(websocket: WebSocket, review_id: int):
    """Real-time analysis progress stream."""
    await websocket.accept()
    try:
        steps = [
            (10, "Parsing source files..."),
            (25, "Running security scan..."),
            (40, "Computing complexity metrics..."),
            (55, "Checking style conventions..."),
            (70, "Detecting code duplication..."),
            (85, "Generating AI insights..."),
            (95, "Finalizing report..."),
            (100, "Analysis complete!"),
        ]
        for pct, msg in steps:
            await websocket.send_json({"progress": pct, "message": msg})
            await asyncio.sleep(0.3)
        await websocket.send_json({"progress": 100, "message": "Done", "done": True})
    except WebSocketDisconnect:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZERS
# ─────────────────────────────────────────────────────────────────────────────

def _ser_review(r: Review, detailed: bool = False) -> dict:
    base = {
        "id": r.id, "title": r.title, "status": r.status,
        "quality_score": r.quality_score,
        "maintainability_index": r.maintainability_index,
        "total_issues": r.total_issues,
        "critical_issues": r.critical_issues, "error_issues": r.error_issues,
        "warning_issues": r.warning_issues, "info_issues": r.info_issues,
        "total_lines": r.total_lines, "total_files": r.total_files,
        "avg_complexity": r.avg_complexity, "duplication_pct": r.duplication_pct,
        "ai_summary": r.ai_summary, "ai_praise": r.ai_praise,
        "ai_top_priority": r.ai_top_priority,
        "analysis_duration_ms": r.analysis_duration_ms,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
    }
    if detailed and r.files:
        base["files"] = [
            {
                "id": f.id, "filename": f.filename, "language": f.language,
                "lines_of_code": f.lines_of_code, "blank_lines": f.blank_lines,
                "comment_lines": f.comment_lines,
                "cyclomatic_complexity": f.cyclomatic_complexity,
                "cognitive_complexity": f.cognitive_complexity,
                "maintainability_index": f.maintainability_index,
                "halstead_volume": f.halstead_volume,
                "issue_count": f.issue_count, "quality_score": f.quality_score,
                "annotations": f.annotations,
                "content": f.content,
                "issues": [_ser_issue(i) for i in (f.issues or [])],
            }
            for f in r.files
        ]
    return base


def _ser_issue(i: Issue) -> dict:
    return {
        "id": i.id, "severity": i.severity, "category": i.category,
        "rule_id": i.rule_id, "title": i.title, "message": i.message,
        "line_start": i.line_start, "line_end": i.line_end,
        "column_start": i.column_start, "code_snippet": i.code_snippet,
        "is_fixable": i.is_fixable, "fix_description": i.fix_description,
        "fix_code_snippet": i.fix_code_snippet,
        "is_acknowledged": i.is_acknowledged,
        "suggestions": [
            {"id": s.id, "title": s.title, "explanation": s.explanation,
             "before_code": s.before_code, "after_code": s.after_code,
             "confidence": s.confidence}
            for s in (i.suggestions or [])
        ],
    }
