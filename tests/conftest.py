"""Shared pytest fixtures for the Wine Sommelier test suite."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Inject required env vars so config loads without a real .env file."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    monkeypatch.setenv("PINECONE_API_KEY", "test-pinecone-key")
    monkeypatch.setenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
    monkeypatch.setenv("JWT_SECRET_KEY", "super-secret-test-key-32chars-long!!")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_wine.db")


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """Create a fresh SQLite DB for the test session and drop it after."""
    import os
    from app.models.database import create_tables, engine
    from app.models.db_models import Base
    create_tables()
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_wine.db"):
        os.remove("test_wine.db")
