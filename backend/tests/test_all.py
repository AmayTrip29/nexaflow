"""
NexaFlow — Comprehensive Test Suite
Run: pytest tests/ -v --tb=short
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from urllib.parse import urlencode
import io

from app.main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client):
    resp = await client.post(
        "/api/auth/login",
        content=urlencode({"username": "demo", "password": "demo123"}),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def alex_headers(client):
    resp = await client.post(
        "/api/auth/login",
        content=urlencode({"username": "alex", "password": "alex123"}),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "NexaFlow"


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


# ── Auth ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client):
    resp = await client.post(
        "/api/auth/login",
        content=urlencode({"username": "alex", "password": "alex123"}),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "alex"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post(
        "/api/auth/login",
        content=urlencode({"username": "alex", "password": "wrongpassword"}),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client):
    resp = await client.post(
        "/api/auth/login",
        content=urlencode({"username": "nobody", "password": "anything"}),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_new_user(client):
    resp = await client.post("/api/auth/register", json={
        "username": "testuser_unique_xyz",
        "email": "testunique@nexaflow.dev",
        "password": "securepass123",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    resp = await client.post("/api/auth/register", json={
        "username": "alex",
        "email": "newemail@test.com",
        "password": "pass123",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    resp = await client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "username" in data
    assert "quality_score" in data
    assert "badges" in data
    assert isinstance(data["badges"], list)


@pytest.mark.asyncio
async def test_unauthorized_no_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


# ── Reviews ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_reviews(client, auth_headers):
    resp = await client.get("/api/reviews/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "reviews" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_reviews_alex(client, alex_headers):
    resp = await client.get("/api/reviews/", headers=alex_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2  # seeded with 2 reviews for alex


@pytest.mark.asyncio
async def test_create_review_python(client, auth_headers):
    code = b'''
def calculate(x, y):
    password = "admin123"
    result = []
    for i in range(len(x)):
        result.append(x[i] + y)
    return result
'''
    resp = await client.post(
        "/api/reviews/",
        headers=auth_headers,
        data={"title": "Test Python Review"},
        files=[("files", ("test_calc.py", io.BytesIO(code), "text/plain"))],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "complete"
    assert data["total_issues"] > 0
    assert data["quality_score"] is not None
    assert data["ai_summary"] is not None
    # Should catch hardcoded password and range(len()) at minimum
    assert data["critical_issues"] >= 1


@pytest.mark.asyncio
async def test_create_review_clean_code(client, auth_headers):
    code = b'''"""
Clean module for mathematical operations.
"""
import logging

logger = logging.getLogger(__name__)


def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return the result.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Sum of a and b.
    """
    result = a + b
    logger.info("Computed: %s + %s = %s", a, b, result)
    return result


def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Product of a and b.
    """
    return a * b
'''
    resp = await client.post(
        "/api/reviews/",
        headers=auth_headers,
        data={"title": "Clean Code Review"},
        files=[("files", ("math_utils.py", io.BytesIO(code), "text/plain"))],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["quality_score"] > 70  # clean code should score high
    assert data["critical_issues"] == 0


@pytest.mark.asyncio
async def test_create_review_multiple_files(client, auth_headers):
    file1 = b'def foo():\n    pass\n'
    file2 = b'def bar():\n    x = eval("1+1")\n    return x\n'
    resp = await client.post(
        "/api/reviews/",
        headers=auth_headers,
        data={"title": "Multi-file Review"},
        files=[
            ("files", ("module_a.py", io.BytesIO(file1), "text/plain")),
            ("files", ("module_b.py", io.BytesIO(file2), "text/plain")),
        ],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_files"] == 2


@pytest.mark.asyncio
async def test_get_review_detail(client, alex_headers):
    # List to get an ID
    list_resp = await client.get("/api/reviews/", headers=alex_headers)
    reviews = list_resp.json()["reviews"]
    assert len(reviews) > 0
    review_id = reviews[0]["id"]

    resp = await client.get(f"/api/reviews/{review_id}", headers=alex_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == review_id
    assert "files" in data


@pytest.mark.asyncio
async def test_get_review_not_found(client, auth_headers):
    resp = await client.get("/api/reviews/99999", headers=auth_headers)
    assert resp.status_code == 404


# ── Issues ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_review_issues(client, alex_headers):
    list_resp = await client.get("/api/reviews/", headers=alex_headers)
    reviews = list_resp.json()["reviews"]
    review_id = reviews[0]["id"]

    resp = await client.get(f"/api/issues/review/{review_id}", headers=alex_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "issues" in data
    assert isinstance(data["issues"], list)


@pytest.mark.asyncio
async def test_filter_issues_by_severity(client, alex_headers):
    list_resp = await client.get("/api/reviews/", headers=alex_headers)
    reviews = list_resp.json()["reviews"]
    # Find review 2 which has critical issues
    review_id = None
    for r in reviews:
        if r["critical_issues"] > 0:
            review_id = r["id"]
            break
    if review_id:
        resp = await client.get(
            f"/api/issues/review/{review_id}?severity=critical",
            headers=alex_headers,
        )
        assert resp.status_code == 200
        issues = resp.json()["issues"]
        for issue in issues:
            assert issue["severity"] == "critical"


@pytest.mark.asyncio
async def test_filter_fixable_issues(client, alex_headers):
    list_resp = await client.get("/api/reviews/", headers=alex_headers)
    review_id = list_resp.json()["reviews"][0]["id"]

    resp = await client.get(
        f"/api/issues/review/{review_id}?fixable_only=true",
        headers=alex_headers,
    )
    assert resp.status_code == 200
    for issue in resp.json()["issues"]:
        assert issue["is_fixable"] is True


# ── Analytics ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_analytics(client, alex_headers):
    resp = await client.get("/api/analytics/dashboard", headers=alex_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "user" in data
    assert "quality_trend" in data
    assert "issues_by_category" in data
    assert "issues_by_severity" in data
    assert "badges" in data
    assert "stats" in data


@pytest.mark.asyncio
async def test_global_analytics(client):
    resp = await client.get("/api/analytics/global")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert data["total_users"] >= 3  # seeded 3 users
    assert data["total_reviews"] >= 2


# ── Users / Leaderboard ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_leaderboard(client):
    resp = await client.get("/api/users/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "leaderboard" in data
    assert len(data["leaderboard"]) >= 1
    # Should be sorted by quality_score descending
    scores = [e["quality_score"] for e in data["leaderboard"]]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_user_profile(client):
    resp = await client.get("/api/users/alex/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alex"
    assert "badges" in data
    assert "recent_reviews" in data


@pytest.mark.asyncio
async def test_user_profile_not_found(client):
    resp = await client.get("/api/users/doesnotexist_xyz/profile")
    assert resp.status_code == 404


# ── Repositories ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_repos(client, alex_headers):
    resp = await client.get("/api/repos/", headers=alex_headers)
    assert resp.status_code == 200
    assert "repositories" in resp.json()


@pytest.mark.asyncio
async def test_create_repo(client, auth_headers):
    resp = await client.post("/api/repos/", headers=auth_headers, json={
        "name": "my-test-repo",
        "description": "Test repository",
        "language": "python",
        "is_public": True,
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "my-test-repo"


# ── Analyzer Unit Tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyzer_detects_eval():
    from app.analyzer.engine import CodeAnalyzer
    analyzer = CodeAnalyzer()
    metrics = await analyzer.analyze({"test.py": 'result = eval(user_input)\n'})
    rule_ids = [i.rule_id for f in metrics.per_file.values() for i in f.issues]
    assert "SEC001" in rule_ids


@pytest.mark.asyncio
async def test_analyzer_detects_hardcoded_password():
    from app.analyzer.engine import CodeAnalyzer
    analyzer = CodeAnalyzer()
    metrics = await analyzer.analyze({"config.py": 'password = "supersecret123"\n'})
    rule_ids = [i.rule_id for f in metrics.per_file.values() for i in f.issues]
    assert "SEC008" in rule_ids


@pytest.mark.asyncio
async def test_analyzer_detects_bare_except():
    from app.analyzer.engine import CodeAnalyzer
    analyzer = CodeAnalyzer()
    code = 'try:\n    do_something()\nexcept:\n    pass\n'
    metrics = await analyzer.analyze({"handlers.py": code})
    rule_ids = [i.rule_id for f in metrics.per_file.values() for i in f.issues]
    assert "STYLE001" in rule_ids


@pytest.mark.asyncio
async def test_analyzer_detects_sql_injection():
    from app.analyzer.engine import CodeAnalyzer
    analyzer = CodeAnalyzer()
    code = 'query = "SELECT * FROM users WHERE id = " + str(user_id)\n'
    metrics = await analyzer.analyze({"db.py": code})
    rule_ids = [i.rule_id for f in metrics.per_file.values() for i in f.issues]
    assert "SEC011" in rule_ids


@pytest.mark.asyncio
async def test_analyzer_detects_mutable_default():
    from app.analyzer.engine import CodeAnalyzer
    analyzer = CodeAnalyzer()
    code = 'def add_item(item, items=[]):\n    items.append(item)\n    return items\n'
    metrics = await analyzer.analyze({"utils.py": code})
    rule_ids = [i.rule_id for f in metrics.per_file.values() for i in f.issues]
    assert "AST003" in rule_ids


@pytest.mark.asyncio
async def test_analyzer_quality_score_range():
    from app.analyzer.engine import CodeAnalyzer
    analyzer = CodeAnalyzer()
    metrics = await analyzer.analyze({"any.py": "x = 1\n"})
    assert 0 <= metrics.quality_score <= 100


@pytest.mark.asyncio
async def test_analyzer_syntax_error_handled():
    from app.analyzer.engine import CodeAnalyzer
    analyzer = CodeAnalyzer()
    bad_code = "def broken(\n    this is not python\n"
    metrics = await analyzer.analyze({"broken.py": bad_code})
    rule_ids = [i.rule_id for f in metrics.per_file.values() for i in f.issues]
    assert "SYNTAX001" in rule_ids


@pytest.mark.asyncio
async def test_analyzer_generates_summary():
    from app.analyzer.engine import CodeAnalyzer
    analyzer = CodeAnalyzer()
    metrics = await analyzer.analyze({"main.py": 'x = 1\ny = 2\nz = x + y\n'})
    assert metrics.ai_summary
    assert metrics.ai_praise
    assert metrics.ai_top_priority


@pytest.mark.asyncio
async def test_analyzer_multi_file_duplication():
    from app.analyzer.engine import CodeAnalyzer
    analyzer = CodeAnalyzer()
    duplicate_code = 'def process(x):\n    return x * 2\n'
    metrics = await analyzer.analyze({
        "module_a.py": duplicate_code,
        "module_b.py": duplicate_code,
    })
    assert metrics.duplication_pct > 0


@pytest.mark.asyncio
async def test_maintainability_index_range():
    from app.analyzer.engine import compute_maintainability_index
    mi = compute_maintainability_index(1000.0, 5.0, 100, 0.2)
    assert 0 <= mi <= 100


@pytest.mark.asyncio
async def test_halstead_volume_positive():
    from app.analyzer.engine import compute_halstead
    vol = compute_halstead("x = a + b * c\nif x > 0:\n    return x\n")
    assert vol >= 0
