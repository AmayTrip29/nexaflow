"""
NexaFlow — Database Models

Entities:
  User          — developer accounts
  Repository    — tracked code repos / projects
  Review        — a code review session (one or many files)
  ReviewFile    — individual file within a review
  Issue         — a single code issue found by analysis
  Suggestion    — AI-generated fix suggestion for an issue
  Badge         — gamification achievement earned by a user
  UserBadge     — junction: user ↔ badge
"""

from datetime import datetime
from typing import Optional
import enum
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, Enum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class IssueSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueCategory(str, enum.Enum):
    STYLE = "style"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    BUG = "bug"
    DOCUMENTATION = "documentation"
    DUPLICATION = "duplication"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    FAILED = "failed"


class Language(str, enum.Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"


# ─── User ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(300), nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Stats (denormalized for fast dashboard)
    total_reviews = Column(Integer, default=0)
    total_issues_found = Column(Integer, default=0)
    total_issues_fixed = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)   # 0–100, rolling average
    streak_days = Column(Integer, default=0)

    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    repositories = relationship("Repository", back_populates="owner", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="author", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")


# ─── Repository ───────────────────────────────────────────────────────────────

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(Enum(Language), default=Language.PYTHON)
    is_public = Column(Boolean, default=True)

    # Aggregated metrics
    total_reviews = Column(Integer, default=0)
    avg_quality_score = Column(Float, default=0.0)
    total_issues = Column(Integer, default=0)
    issues_by_severity = Column(JSON, default=dict)
    issues_by_category = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="repositories")
    reviews = relationship("Review", back_populates="repository", cascade="all, delete-orphan")


# ─── Review ───────────────────────────────────────────────────────────────────

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(300), nullable=False)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING)

    # Results
    quality_score = Column(Float, nullable=True)        # 0–100
    maintainability_index = Column(Float, nullable=True)
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    error_issues = Column(Integer, default=0)
    warning_issues = Column(Integer, default=0)
    info_issues = Column(Integer, default=0)

    # Aggregate metrics
    total_lines = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    avg_complexity = Column(Float, nullable=True)
    duplication_pct = Column(Float, nullable=True)
    test_coverage_estimate = Column(Float, nullable=True)

    # AI summary
    ai_summary = Column(Text, nullable=True)
    ai_praise = Column(Text, nullable=True)        # what's good
    ai_top_priority = Column(Text, nullable=True)  # most important fix

    analysis_duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    author = relationship("User", back_populates="reviews")
    repository = relationship("Repository", back_populates="reviews")
    files = relationship("ReviewFile", back_populates="review", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="review", cascade="all, delete-orphan")


# ─── ReviewFile ───────────────────────────────────────────────────────────────

class ReviewFile(Base):
    __tablename__ = "review_files"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(500), nullable=False)
    language = Column(Enum(Language), default=Language.PYTHON)
    content = Column(Text, nullable=False)

    # Per-file metrics
    lines_of_code = Column(Integer, default=0)
    blank_lines = Column(Integer, default=0)
    comment_lines = Column(Integer, default=0)
    cyclomatic_complexity = Column(Float, nullable=True)
    cognitive_complexity = Column(Float, nullable=True)
    maintainability_index = Column(Float, nullable=True)
    halstead_volume = Column(Float, nullable=True)
    issue_count = Column(Integer, default=0)
    quality_score = Column(Float, nullable=True)

    # Highlighted / annotated content (JSON: line -> [issues])
    annotations = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    review = relationship("Review", back_populates="files")
    issues = relationship("Issue", back_populates="file", cascade="all, delete-orphan")


# ─── Issue ────────────────────────────────────────────────────────────────────

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(Integer, ForeignKey("review_files.id", ondelete="CASCADE"), nullable=False)

    severity = Column(Enum(IssueSeverity), nullable=False)
    category = Column(Enum(IssueCategory), nullable=False)
    rule_id = Column(String(100), nullable=False)   # e.g. "C0301", "SEC001", "PERF003"
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)

    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    column_start = Column(Integer, nullable=True)
    column_end = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)

    # Fix
    is_fixable = Column(Boolean, default=False)
    fix_description = Column(Text, nullable=True)
    fix_code_snippet = Column(Text, nullable=True)

    # State
    is_acknowledged = Column(Boolean, default=False)
    is_false_positive = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    review = relationship("Review", back_populates="issues")
    file = relationship("ReviewFile", back_populates="issues")
    suggestions = relationship("Suggestion", back_populates="issue", cascade="all, delete-orphan")


# ─── Suggestion ───────────────────────────────────────────────────────────────

class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False)
    explanation = Column(Text, nullable=False)
    before_code = Column(Text, nullable=True)
    after_code = Column(Text, nullable=True)
    confidence = Column(Float, default=0.8)   # 0–1
    is_applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    issue = relationship("Issue", back_populates="suggestions")


# ─── Badge ────────────────────────────────────────────────────────────────────

class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(10), nullable=False)      # emoji
    color = Column(String(20), default="#6366f1")
    criteria_json = Column(JSON, default=dict)     # threshold info

    users = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (UniqueConstraint("user_id", "badge_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="users")
