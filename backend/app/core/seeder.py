"""Seeds NexaFlow database with demo users, repos, and reviews."""

import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.auth import hash_password
from app.models.models import User, Repository, Review, ReviewFile, Issue, Suggestion, Badge, UserBadge, ReviewStatus, Language, IssueSeverity, IssueCategory

logger = logging.getLogger(__name__)

SAMPLE_PYTHON_CODE_GOOD = '''"""
User authentication service.
Handles login, token generation, and password management.
"""

import hashlib
import secrets
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AuthResult:
    """Result of an authentication attempt."""
    success: bool
    user_id: Optional[int] = None
    token: Optional[str] = None
    error: Optional[str] = None


class AuthService:
    """Service for handling user authentication."""

    def __init__(self, db_session, token_ttl: int = 3600):
        """
        Initialize the auth service.

        Args:
            db_session: Database session for user lookups.
            token_ttl: Token time-to-live in seconds.
        """
        self._db = db_session
        self._token_ttl = token_ttl

    def authenticate(self, username: str, password: str) -> AuthResult:
        """
        Authenticate a user with username and password.

        Args:
            username: The user's login name.
            password: The plaintext password to verify.

        Returns:
            AuthResult with success status and token if authenticated.
        """
        if not username or not password:
            return AuthResult(success=False, error="Username and password required")

        user = self._db.get_user(username)
        if not user:
            logger.warning("Login attempt for unknown user: %s", username)
            return AuthResult(success=False, error="Invalid credentials")

        if not self._verify_password(password, user.password_hash):
            logger.warning("Failed login attempt for user: %s", username)
            return AuthResult(success=False, error="Invalid credentials")

        token = secrets.token_urlsafe(32)
        logger.info("User %s authenticated successfully", username)
        return AuthResult(success=True, user_id=user.id, token=token)

    def _verify_password(self, plain: str, hashed: str) -> bool:
        """Verify a plaintext password against its hash."""
        computed = hashlib.sha256(plain.encode()).hexdigest()
        return secrets.compare_digest(computed, hashed)
'''

SAMPLE_PYTHON_CODE_BAD = '''import os, sys
from utils import *

password = "admin123"
API_KEY = "sk-1234567890abcdef"

def ProcessUserData(data, flag1, flag2, flag3, flag4, flag5, flag6, flag7, flag8):
    result = []
    for i in range(len(data)):
        item = data[i]
        if flag1 == True:
            if flag2 == True:
                if flag3 == True:
                    if item["active"] == True:
                        try:
                            processed = eval(item["expr"])
                            result.append(processed)
                        except:
                            pass
                        if flag4 == True:
                            x = os.system("echo " + item["name"])
                            if x == 0:
                                result.append(item)
    return result

def fetch_data(url):
    import urllib.request
    data = urllib.request.urlopen(url).read()
    return data

class user_manager:
    def getUser(self, id):
        query = "SELECT * FROM users WHERE id = " + str(id)
        return self.db.execute(query)
    
    def saveUser(self, users=[]):
        for u in users:
            self.db.save(u)
'''

BADGES_DATA = [
    {
        "slug": "first-review", "name": "First Review", "icon": "🔍",
        "description": "Completed your first code review.", "color": "#6366f1",
        "criteria_json": {"reviews": 1},
    },
    {
        "slug": "code-guardian", "name": "Code Guardian", "icon": "🛡️",
        "description": "Completed 10 code reviews.", "color": "#8b5cf6",
        "criteria_json": {"reviews": 10},
    },
    {
        "slug": "security-hawk", "name": "Security Hawk", "icon": "🦅",
        "description": "Found 5 critical security issues.", "color": "#ef4444",
        "criteria_json": {"critical_found": 5},
    },
    {
        "slug": "clean-coder", "name": "Clean Coder", "icon": "✨",
        "description": "Achieved a quality score of 90+ on a review.", "color": "#10b981",
        "criteria_json": {"quality_score": 90},
    },
    {
        "slug": "refactor-king", "name": "Refactor King", "icon": "👑",
        "description": "Fixed 20 issues across all reviews.", "color": "#f59e0b",
        "criteria_json": {"issues_fixed": 20},
    },
    {
        "slug": "streak-3", "name": "On a Roll", "icon": "🔥",
        "description": "Reviewed code 3 days in a row.", "color": "#f97316",
        "criteria_json": {"streak_days": 3},
    },
]


async def seed_database():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        if result.scalar():
            logger.info("Database already seeded — skipping")
            return

        logger.info("Seeding NexaFlow database...")

        # ── Badges ────────────────────────────────────────────────────────────
        badges = [Badge(**b) for b in BADGES_DATA]
        db.add_all(badges)
        await db.flush()

        # ── Users ─────────────────────────────────────────────────────────────
        now = datetime.utcnow()
        users = [
            User(
                username="alex", email="alex@example.com",
                hashed_password=hash_password("alex123"),
                full_name="Alex Sharma", is_active=True, is_verified=True,
                bio="Senior Software Engineer | Python & TypeScript | Clean Code Advocate",
                total_reviews=12, total_issues_found=87, total_issues_fixed=54,
                quality_score=82.5, streak_days=5, last_login=now,
            ),
            User(
                username="priya", email="priya@example.com",
                hashed_password=hash_password("priya123"),
                full_name="Priya Nair", is_active=True, is_verified=True,
                bio="Full Stack Developer | React + FastAPI",
                total_reviews=7, total_issues_found=41, total_issues_fixed=30,
                quality_score=76.0, streak_days=2, last_login=now - timedelta(days=1),
            ),
            User(
                username="demo", email="demo@nexaflow.dev",
                hashed_password=hash_password("demo123"),
                full_name="Demo User", is_active=True, is_verified=True,
                bio="Try NexaFlow — AI-powered code review",
                total_reviews=3, total_issues_found=22, total_issues_fixed=8,
                quality_score=68.0, streak_days=1, last_login=now,
            ),
        ]
        db.add_all(users)
        await db.flush()

        # Assign badges
        badge_map = {b.slug: b for b in badges}
        db.add(UserBadge(user_id=users[0].id, badge_id=badge_map["first-review"].id,
                          earned_at=now - timedelta(days=30)))
        db.add(UserBadge(user_id=users[0].id, badge_id=badge_map["code-guardian"].id,
                          earned_at=now - timedelta(days=10)))
        db.add(UserBadge(user_id=users[0].id, badge_id=badge_map["clean-coder"].id,
                          earned_at=now - timedelta(days=5)))
        db.add(UserBadge(user_id=users[0].id, badge_id=badge_map["streak-3"].id,
                          earned_at=now - timedelta(days=2)))
        db.add(UserBadge(user_id=users[1].id, badge_id=badge_map["first-review"].id,
                          earned_at=now - timedelta(days=15)))
        db.add(UserBadge(user_id=users[2].id, badge_id=badge_map["first-review"].id,
                          earned_at=now - timedelta(days=5)))
        await db.flush()

        # ── Repositories ──────────────────────────────────────────────────────
        repos = [
            Repository(
                owner_id=users[0].id, name="auth-service",
                description="JWT authentication microservice for the platform",
                language=Language.PYTHON, is_public=True,
                total_reviews=5, avg_quality_score=81.0,
                total_issues=43, issues_by_severity={"critical": 2, "error": 8, "warning": 18, "info": 15},
            ),
            Repository(
                owner_id=users[0].id, name="api-gateway",
                description="Central API gateway with rate limiting and routing",
                language=Language.PYTHON, is_public=True,
                total_reviews=3, avg_quality_score=74.0,
                total_issues=29, issues_by_severity={"critical": 1, "error": 5, "warning": 12, "info": 11},
            ),
            Repository(
                owner_id=users[1].id, name="frontend-react",
                description="React TypeScript frontend application",
                language=Language.TYPESCRIPT, is_public=True,
                total_reviews=4, avg_quality_score=78.0,
                total_issues=31,
            ),
        ]
        db.add_all(repos)
        await db.flush()

        # ── Reviews ───────────────────────────────────────────────────────────
        # Review 1: good code, high score
        review1 = Review(
            author_id=users[0].id, repository_id=repos[0].id,
            title="auth_service.py — Authentication Module",
            status=ReviewStatus.COMPLETE,
            quality_score=88.0, maintainability_index=78.5,
            total_issues=5, critical_issues=0, error_issues=1,
            warning_issues=2, info_issues=2,
            total_lines=62, total_files=1,
            avg_complexity=3.2, duplication_pct=0.0,
            ai_summary="This is high-quality code demonstrating solid security and readability practices. The AuthService class is well-structured with clear separation of concerns and proper use of secrets module for token generation.",
            ai_praise="Security practices are excellent — using secrets.compare_digest() prevents timing attacks, and token generation uses cryptographically secure randomness.",
            ai_top_priority="✅ Address the 2 warnings and 2 informational suggestions to achieve near-perfect code quality.",
            analysis_duration_ms=312,
            created_at=now - timedelta(days=3),
            completed_at=now - timedelta(days=3),
        )
        db.add(review1)
        await db.flush()

        file1 = ReviewFile(
            review_id=review1.id, filename="auth_service.py",
            language=Language.PYTHON,
            content=SAMPLE_PYTHON_CODE_GOOD,
            lines_of_code=62, blank_lines=12, comment_lines=18,
            cyclomatic_complexity=3.2, cognitive_complexity=4.0,
            maintainability_index=78.5, halstead_volume=1245.6,
            issue_count=5, quality_score=88.0,
            annotations={"44": ["[INFO] Missing docstring"], "51": ["[WARNING] Consider logging"]},
        )
        db.add(file1)
        await db.flush()

        issues_good = [
            Issue(review_id=review1.id, file_id=file1.id, severity=IssueSeverity.INFO,
                  category=IssueCategory.DOCUMENTATION, rule_id="AST002",
                  title="Missing docstring", message="Function '_verify_password' has no docstring.",
                  line_start=44, is_fixable=True,
                  fix_description='Add: """Verify plaintext password against stored hash."""'),
            Issue(review_id=review1.id, file_id=file1.id, severity=IssueSeverity.WARNING,
                  category=IssueCategory.STYLE, rule_id="STYLE004",
                  title="Consider structured logging", message="Use structured logging with extra fields for better observability.",
                  line_start=51, is_fixable=True,
                  fix_description='logger.info("Authenticated", extra={"user_id": user.id})'),
            Issue(review_id=review1.id, file_id=file1.id, severity=IssueSeverity.ERROR,
                  category=IssueCategory.SECURITY, rule_id="SEC006",
                  title="Weak hash function used in _verify_password",
                  message="SHA-256 without salt is vulnerable to rainbow table attacks. Use bcrypt or argon2.",
                  line_start=53, is_fixable=True,
                  fix_description="Use passlib:\n  from passlib.context import CryptContext\n  pwd_ctx = CryptContext(schemes=['bcrypt'])\n  pwd_ctx.verify(plain, hashed)"),
        ]
        db.add_all(issues_good)
        await db.flush()

        db.add(Suggestion(
            issue_id=issues_good[2].id,
            title="Switch to bcrypt for password hashing",
            explanation="SHA-256 is a fast hash, making brute-force attacks feasible. bcrypt is specifically designed for passwords with an adjustable cost factor.",
            before_code="return hashlib.sha256(plain.encode()).hexdigest() == hashed",
            after_code="from passlib.context import CryptContext\npwd_ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')\nreturn pwd_ctx.verify(plain, hashed)",
            confidence=0.97,
        ))

        # Review 2: bad code, low score
        review2 = Review(
            author_id=users[0].id, repository_id=repos[0].id,
            title="data_processor.py — User Data Processing",
            status=ReviewStatus.COMPLETE,
            quality_score=28.0, maintainability_index=41.2,
            total_issues=18, critical_issues=5, error_issues=4,
            warning_issues=6, info_issues=3,
            total_lines=45, total_files=1,
            avg_complexity=11.0, duplication_pct=0.0,
            ai_summary="Critical code quality issues detected — scored 28/100. 5 critical security vulnerabilities including hardcoded credentials, eval() usage, and SQL injection risk require immediate remediation before any deployment.",
            ai_praise="Functions are short and focused, which is a positive trait despite the issues found.",
            ai_top_priority="🚨 Fix 5 critical security issues immediately — hardcoded credentials and eval() make this code actively dangerous.",
            analysis_duration_ms=445,
            created_at=now - timedelta(days=1),
            completed_at=now - timedelta(days=1),
        )
        db.add(review2)
        await db.flush()

        file2 = ReviewFile(
            review_id=review2.id, filename="data_processor.py",
            language=Language.PYTHON,
            content=SAMPLE_PYTHON_CODE_BAD,
            lines_of_code=45, blank_lines=8, comment_lines=0,
            cyclomatic_complexity=11.0, cognitive_complexity=16.0,
            maintainability_index=41.2, halstead_volume=3420.0,
            issue_count=18, quality_score=28.0,
            annotations={
                "4": ["[CRITICAL] Hardcoded password"],
                "5": ["[CRITICAL] Hardcoded API key"],
                "7": ["[WARNING] Function name not snake_case", "[WARNING] Too many parameters"],
                "14": ["[CRITICAL] Dangerous eval() usage"],
                "17": ["[CRITICAL] os.system shell injection"],
                "26": ["[CRITICAL] SQL injection risk"],
            },
        )
        db.add(file2)
        await db.flush()

        issues_bad = [
            Issue(review_id=review2.id, file_id=file2.id, severity=IssueSeverity.CRITICAL,
                  category=IssueCategory.SECURITY, rule_id="SEC008",
                  title="Hardcoded password in source code",
                  message='password = "admin123" — credentials must never be in source code. Use environment variables.',
                  line_start=4, code_snippet='password = "admin123"',
                  is_fixable=True,
                  fix_description='import os\npassword = os.environ.get("DB_PASSWORD")',
                  fix_code_snippet='import os\npassword = os.environ.get("DB_PASSWORD")'),
            Issue(review_id=review2.id, file_id=file2.id, severity=IssueSeverity.CRITICAL,
                  category=IssueCategory.SECURITY, rule_id="SEC010",
                  title="Hardcoded API key", message='API_KEY literal in source. Will be exposed in version control.',
                  line_start=5, code_snippet='API_KEY = "sk-1234567890abcdef"',
                  is_fixable=True, fix_description='API_KEY = os.environ.get("API_KEY")'),
            Issue(review_id=review2.id, file_id=file2.id, severity=IssueSeverity.CRITICAL,
                  category=IssueCategory.SECURITY, rule_id="SEC001",
                  title="Dangerous eval() usage",
                  message='eval(item["expr"]) executes arbitrary user-supplied code. Remote code execution vulnerability.',
                  line_start=14, code_snippet='processed = eval(item["expr"])',
                  is_fixable=True, fix_description='Use ast.literal_eval() for safe parsing:\n  import ast\n  processed = ast.literal_eval(item["expr"])'),
            Issue(review_id=review2.id, file_id=file2.id, severity=IssueSeverity.CRITICAL,
                  category=IssueCategory.SECURITY, rule_id="SEC004",
                  title="os.system() shell injection risk",
                  message='os.system("echo " + item["name"]) — user input fed to shell. Command injection vulnerability.',
                  line_start=17, code_snippet='x = os.system("echo " + item["name"])',
                  is_fixable=True,
                  fix_description='import subprocess\nresult = subprocess.run(["echo", item["name"]], capture_output=True)'),
            Issue(review_id=review2.id, file_id=file2.id, severity=IssueSeverity.CRITICAL,
                  category=IssueCategory.SECURITY, rule_id="SEC011",
                  title="SQL injection vulnerability",
                  message='String concatenation in SQL query. Attacker can inject malicious SQL.',
                  line_start=26, code_snippet='"SELECT * FROM users WHERE id = " + str(id)',
                  is_fixable=True, fix_description='cursor.execute("SELECT * FROM users WHERE id = ?", (id,))'),
            Issue(review_id=review2.id, file_id=file2.id, severity=IssueSeverity.WARNING,
                  category=IssueCategory.STYLE, rule_id="PERF006",
                  title="Wildcard import", message="'from utils import *' pollutes namespace and hides dependencies.",
                  line_start=2, is_fixable=True, fix_description='Import explicitly: from utils import needed_func'),
            Issue(review_id=review2.id, file_id=file2.id, severity=IssueSeverity.WARNING,
                  category=IssueCategory.MAINTAINABILITY, rule_id="AST005",
                  title="Too many parameters (9)",
                  message="ProcessUserData has 9 parameters. Use a dataclass for configuration.",
                  line_start=7, is_fixable=True,
                  fix_description='@dataclass\nclass ProcessConfig:\n    flag1: bool\n    flag2: bool\n    ...\n\ndef process_user_data(data: list, config: ProcessConfig): ...'),
            Issue(review_id=review2.id, file_id=file2.id, severity=IssueSeverity.ERROR,
                  category=IssueCategory.STYLE, rule_id="STYLE001",
                  title="Bare except clause",
                  message="except: catches ALL exceptions including SystemExit. Specify exception types.",
                  line_start=15, is_fixable=True,
                  fix_description='except (ValueError, KeyError) as e:\n    logger.error("Processing error: %s", e)'),
            Issue(review_id=review2.id, file_id=file2.id, severity=IssueSeverity.ERROR,
                  category=IssueCategory.COMPLEXITY, rule_id="COMP001",
                  title="High cyclomatic complexity (11)",
                  message="ProcessUserData has cyclomatic complexity of 11. Break into smaller functions.",
                  line_start=7, is_fixable=False),
        ]
        db.add_all(issues_bad)
        await db.flush()

        db.add(Suggestion(
            issue_id=issues_bad[0].id,
            title="Use environment variables for credentials",
            explanation="Hardcoded credentials in source code are exposed in git history and to anyone with repo access.",
            before_code='password = "admin123"',
            after_code='import os\nfrom dotenv import load_dotenv\nload_dotenv()\npassword = os.environ.get("DB_PASSWORD")\nif not password:\n    raise ValueError("DB_PASSWORD environment variable not set")',
            confidence=0.99,
        ))
        db.add(Suggestion(
            issue_id=issues_bad[2].id,
            title="Replace eval() with safe alternatives",
            explanation="eval() is one of the most dangerous Python functions. For JSON: use json.loads(). For literals: use ast.literal_eval().",
            before_code='processed = eval(item["expr"])',
            after_code='import ast\nimport json\n\n# For JSON data:\nprocessed = json.loads(item["expr"])\n\n# For Python literals (numbers, strings, lists, dicts):\nprocessed = ast.literal_eval(item["expr"])',
            confidence=0.95,
        ))

        # Review 3: demo user, medium quality
        review3 = Review(
            author_id=users[2].id, repository_id=None,
            title="calculator.py — Demo Review",
            status=ReviewStatus.COMPLETE,
            quality_score=68.0, maintainability_index=72.0,
            total_issues=8, critical_issues=0, error_issues=2,
            warning_issues=3, info_issues=3,
            total_lines=55, total_files=1,
            avg_complexity=5.5, duplication_pct=0.0,
            ai_summary="Code quality is moderate (68/100). The logic is clear but has several style and maintainability issues worth addressing.",
            ai_praise="Good separation of arithmetic operations into individual functions. Easy to extend.",
            ai_top_priority="⚠️ Address 2 error-level issues — bare except and print() statements before production use.",
            analysis_duration_ms=198,
            created_at=now - timedelta(hours=6),
            completed_at=now - timedelta(hours=6),
        )
        db.add(review3)

        await db.commit()
        logger.info("✅ Database seeded — demo data ready")
