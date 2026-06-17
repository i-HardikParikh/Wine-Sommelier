"""Integration tests against the FastAPI app using TestClient.
These mock external services (OpenAI, Pinecone) so no real API keys are needed.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create test client with mocked external services."""
    with (
        patch("app.utils.vector_utils.get_pinecone_index"),
        patch("app.utils.vector_utils.embed_texts", return_value=[[0.1] * 3072]),
        patch("app.utils.vector_utils.query_vectors", return_value=[]),
        patch("app.agent.nodes._llm"),
    ):
        from app.main import app
        with TestClient(app) as c:
            yield c


@pytest.fixture(scope="module")
def auth_token(client):
    """Register a test user and return JWT token."""
    resp = client.post("/auth/register", json={
        "email": "test@sommelier.ai",
        "password": "testpass123",
        "full_name": "Test User",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ─── Health ──────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data

    def test_root_returns_info(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Wine Sommelier" in resp.json()["message"]


# ─── Auth ────────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@sommelier.ai",
            "password": "newpass123",
            "full_name": "New User",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_register_duplicate_email_fails(self, client):
        payload = {"email": "dupe@sommelier.ai", "password": "pass1234", "full_name": "Dupe"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 400

    def test_login_success(self, client, auth_token):
        resp = client.post("/auth/login", json={
            "email": "test@sommelier.ai",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password_fails(self, client):
        resp = client.post("/auth/login", json={
            "email": "test@sommelier.ai",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_me_returns_profile(self, client, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@sommelier.ai"

    def test_protected_route_without_token_fails(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 403


# ─── Chat ────────────────────────────────────────────────────────────────────

class TestChat:
    def test_query_requires_auth(self, client):
        resp = client.post("/chat/query", json={"question": "What wine pairs with steak?"})
        assert resp.status_code == 403

    @patch("app.routers.agent_router.run_query", return_value={
        "answer": "I recommend a Cabernet Sauvignon.",
        "sources": ["wine_guide.pdf"],
        "pipeline_path": ["analyze_query", "vector_search", "answer_synthesis"],
        "latency_ms": 450.0,
        "query_type": "wine_pairing",
    })
    def test_query_returns_answer(self, mock_query, client, auth_headers):
        resp = client.post("/chat/query", json={"question": "What wine pairs with steak?"}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "session_id" in data
        assert len(data["answer"]) > 0

    def test_list_sessions(self, client, auth_headers):
        resp = client.get("/chat/sessions", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ─── Ingest ──────────────────────────────────────────────────────────────────

class TestIngest:
    def test_ingest_requires_auth(self, client):
        resp = client.post("/ingest/document", files={"file": ("test.pdf", b"data", "application/pdf")})
        assert resp.status_code == 403

    def test_ingest_unsupported_type_fails(self, client, auth_headers):
        resp = client.post(
            "/ingest/document",
            files={"file": ("test.txt", b"hello", "text/plain")},
            headers=auth_headers,
        )
        assert resp.status_code == 400
