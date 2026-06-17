"""Unit tests for app.utils.llm_client — OpenAI-first, Groq-fallback policy."""
import pytest
from unittest.mock import patch


class TestLLMClientChat:
    def test_uses_openai_when_available(self):
        from app.utils.llm_client import get_llm_client
        llm = get_llm_client()
        with patch("app.utils.llm_client._call_openai_chat", return_value="OpenAI answer") as mock_openai, \
             patch("app.utils.llm_client._call_groq_chat") as mock_groq:
            result = llm.chat(messages=[{"role": "user", "content": "hi"}])
            assert result == "OpenAI answer"
            mock_openai.assert_called_once()
            mock_groq.assert_not_called()

    def test_falls_back_to_groq_when_openai_fails(self):
        from app.utils.llm_client import get_llm_client
        llm = get_llm_client()
        with patch("app.utils.llm_client._call_openai_chat", side_effect=Exception("rate limited")), \
             patch("app.utils.llm_client._call_groq_chat", return_value="Groq answer") as mock_groq:
            result = llm.chat(messages=[{"role": "user", "content": "hi"}])
            assert result == "Groq answer"
            mock_groq.assert_called_once()

    def test_raises_when_both_providers_fail(self):
        from app.utils.llm_client import get_llm_client, LLMError
        llm = get_llm_client()
        with patch("app.utils.llm_client._call_openai_chat", side_effect=Exception("openai down")), \
             patch("app.utils.llm_client._call_groq_chat", side_effect=Exception("groq down")):
            with pytest.raises(LLMError):
                llm.chat(messages=[{"role": "user", "content": "hi"}])

    def test_never_calls_groq_first_even_if_openai_key_missing_initially(self):
        """OpenAI is always attempted first, regardless of whether it's likely to succeed."""
        from app.utils.llm_client import get_llm_client
        llm = get_llm_client()
        call_order = []

        def fake_openai(*a, **kw):
            call_order.append("openai")
            raise Exception("no key")

        def fake_groq(*a, **kw):
            call_order.append("groq")
            return "groq result"

        with patch("app.utils.llm_client._call_openai_chat", side_effect=fake_openai), \
             patch("app.utils.llm_client._call_groq_chat", side_effect=fake_groq):
            llm.chat(messages=[{"role": "user", "content": "hi"}])
            assert call_order == ["openai", "groq"]


class TestLLMClientJSON:
    def test_chat_json_openai_first(self):
        from app.utils.llm_client import get_llm_client
        llm = get_llm_client()
        with patch("app.utils.llm_client._call_openai_json", return_value='{"score": 0.9}') as mock_openai, \
             patch("app.utils.llm_client._call_groq_json") as mock_groq:
            result = llm.chat_json(messages=[{"role": "user", "content": "judge this"}])
            assert result == '{"score": 0.9}'
            mock_openai.assert_called_once()
            mock_groq.assert_not_called()

    def test_chat_json_falls_back_to_groq(self):
        from app.utils.llm_client import get_llm_client
        llm = get_llm_client()
        with patch("app.utils.llm_client._call_openai_json", side_effect=Exception("down")), \
             patch("app.utils.llm_client._call_groq_json", return_value='{"score": 0.5}') as mock_groq:
            result = llm.chat_json(messages=[{"role": "user", "content": "judge this"}])
            assert result == '{"score": 0.5}'
            mock_groq.assert_called_once()


class TestLLMClientVision:
    def test_vision_uses_openai_first(self):
        from app.utils.llm_client import get_llm_client
        llm = get_llm_client()
        with patch("app.utils.llm_client._call_openai_vision", return_value="vision text") as mock_openai, \
             patch("app.utils.llm_client._call_groq_vision") as mock_groq:
            result = llm.vision(image_b64="abc123", prompt="describe")
            assert result == "vision text"
            mock_openai.assert_called_once()
            mock_groq.assert_not_called()

    def test_vision_falls_back_to_groq(self):
        from app.utils.llm_client import get_llm_client
        llm = get_llm_client()
        with patch("app.utils.llm_client._call_openai_vision", side_effect=Exception("down")), \
             patch("app.utils.llm_client._call_groq_vision", return_value="groq vision text") as mock_groq:
            result = llm.vision(image_b64="abc123", prompt="describe")
            assert result == "groq vision text"
            mock_groq.assert_called_once()

    def test_vision_returns_empty_string_when_both_fail(self):
        """Vision is best-effort — should not raise, just return ''."""
        from app.utils.llm_client import get_llm_client
        llm = get_llm_client()
        with patch("app.utils.llm_client._call_openai_vision", side_effect=Exception("down")), \
             patch("app.utils.llm_client._call_groq_vision", side_effect=Exception("also down")):
            result = llm.vision(image_b64="abc123", prompt="describe")
            assert result == ""


class TestProviderUnavailable:
    def test_openai_chat_raises_provider_unavailable_without_key(self, monkeypatch):
        from app.models.config import get_config
        get_config.cache_clear()
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")

        from app.utils.llm_client import _call_openai_chat, ProviderUnavailable
        with pytest.raises(ProviderUnavailable):
            _call_openai_chat([{"role": "user", "content": "hi"}], "gpt-4o-mini", 100, 0.5)

    def test_groq_chat_raises_provider_unavailable_without_key(self, monkeypatch):
        from app.models.config import get_config
        get_config.cache_clear()
        monkeypatch.setenv("GROQ_API_KEY", "")

        from app.utils.llm_client import _call_groq_chat, ProviderUnavailable
        with pytest.raises(ProviderUnavailable):
            _call_groq_chat([{"role": "user", "content": "hi"}], "llama-3.3-70b-versatile", 100, 0.5)
