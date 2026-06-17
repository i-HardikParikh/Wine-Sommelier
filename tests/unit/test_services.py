"""Unit tests for core services — no external API calls required."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


# ─── chunking_utils ──────────────────────────────────────────────────────────

class TestChunkingUtils:
    def test_chunk_text_returns_list(self):
        from app.utils.chunking_utils import chunk_text
        chunks = chunk_text("Hello world. " * 100, source="test.pdf", page=1)
        assert isinstance(chunks, list)
        assert len(chunks) > 0

    def test_chunk_has_required_fields(self):
        from app.utils.chunking_utils import chunk_text
        chunks = chunk_text("Wine is great." * 50, source="wine.pdf", page=2)
        for chunk in chunks:
            assert "id" in chunk
            assert "text" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["source"] == "wine.pdf"
            assert chunk["metadata"]["page"] == 2

    def test_empty_text_returns_empty_list(self):
        from app.utils.chunking_utils import chunk_text
        chunks = chunk_text("   ", source="empty.pdf", page=1)
        assert chunks == []

    def test_chunk_documents_aggregates(self):
        from app.utils.chunking_utils import chunk_documents
        docs = [
            {"text": "Wine A " * 50, "source": "a.pdf", "page": 1, "chunk_type": "text"},
            {"text": "Wine B " * 50, "source": "b.pdf", "page": 2, "chunk_type": "text"},
        ]
        all_chunks = chunk_documents(docs)
        assert len(all_chunks) >= 2


# ─── auth_service ────────────────────────────────────────────────────────────

class TestAuthService:
    def test_hash_and_verify_password(self):
        from app.services.auth_service import hash_password, verify_password
        hashed = hash_password("mysecretpassword")
        assert verify_password("mysecretpassword", hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_create_and_decode_token(self):
        from app.services.auth_service import create_access_token, decode_token
        token = create_access_token({"sub": "42"})
        payload = decode_token(token)
        assert payload["sub"] == "42"

    def test_invalid_token_raises(self):
        from app.services.auth_service import decode_token
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_token("not.a.valid.token")

    def test_create_user_duplicate_raises(self):
        from app.services.auth_service import create_user
        from app.models.schemas import UserRegisterRequest
        from fastapi import HTTPException

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock()  # user exists

        with pytest.raises(HTTPException) as exc:
            create_user(db, UserRegisterRequest(email="a@b.com", password="password1", full_name="Test"))
        assert exc.value.status_code == 400


# ─── conversation_service ────────────────────────────────────────────────────

class TestConversationService:
    def test_get_or_create_session_creates_new(self):
        from app.services.conversation_service import get_or_create_session
        from app.models.db_models import Conversation

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_or_create_session(db, user_id=1)
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_save_message_persists(self):
        from app.services.conversation_service import save_message

        db = MagicMock()
        save_message(db, conversation_id=1, role="user", content="Hello wine!")
        db.add.assert_called_once()
        db.commit.assert_called_once()


# ─── enums ───────────────────────────────────────────────────────────────────

class TestEnums:
    def test_query_type_values(self):
        from app.models.enums import QueryType
        assert QueryType.WINE_PAIRING == "wine_pairing"
        assert QueryType.GENERAL == "general"

    def test_eval_metric_values(self):
        from app.models.enums import EvalMetric
        assert EvalMetric.RELEVANCE == "relevance"
        assert EvalMetric.SOMMELIER_TONE == "sommelier_tone"
