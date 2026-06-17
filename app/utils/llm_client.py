"""
Unified LLM client with automatic provider fallback.

Policy (fixed, not configurable per-call):
    1. ALWAYS try OpenAI first.
    2. If OpenAI is unavailable (no key, auth error, rate limit, timeout,
       5xx, etc.) AND a Groq API key is configured, fall back to Groq.
    3. If neither works, raise LLMError.

This file replaces direct `from openai import OpenAI` calls scattered across
nodes.py, vision_utils.py, and eval_service.py with a single chat()/vision()
interface so the fallback logic lives in exactly one place.

Usage:
    from app.utils.llm_client import get_llm_client
    llm = get_llm_client()
    text = llm.chat(messages=[...], max_tokens=500, kind="agent")
    text = llm.vision(image_b64="...", prompt="...", kind="vision")
"""
from typing import List, Dict, Optional
from loguru import logger

from app.models.config import get_config

class ConfigProxy:
    def __getattr__(self, name):
        return getattr(get_config(), name)

config = ConfigProxy()



class LLMError(Exception):
    """Raised when both OpenAI and Groq fail (or neither is configured)."""
    pass


class ProviderUnavailable(Exception):
    """Internal signal: this provider can't be used (no key, etc). Triggers fallback."""
    pass


# ─── OpenAI calls ────────────────────────────────────────────────────────────

def _openai_client():
    if not config.openai_api_key:
        raise ProviderUnavailable("OPENAI_API_KEY is not set.")
    from openai import OpenAI
    return OpenAI(api_key=config.openai_api_key)


def _call_openai_chat(messages: List[Dict], model: str, max_tokens: int, temperature: float) -> str:
    client = _openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def _call_openai_vision(image_b64: str, prompt: str, model: str, max_tokens: int) -> str:
    client = _openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}", "detail": "high"}},
                {"type": "text", "text": prompt},
            ],
        }],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def _call_openai_json(messages: List[Dict], model: str, max_tokens: int) -> str:
    client = _openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or "{}"


# ─── Groq calls (fallback) ───────────────────────────────────────────────────

def _groq_client():
    if not config.groq_api_key:
        raise ProviderUnavailable("GROQ_API_KEY is not set — cannot fall back.")
    from groq import Groq
    return Groq(api_key=config.groq_api_key)


def _call_groq_chat(messages: List[Dict], model: str, max_tokens: int, temperature: float) -> str:
    client = _groq_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def _call_groq_vision(image_b64: str, prompt: str, model: str, max_tokens: int) -> str:
    client = _groq_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            ],
        }],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def _call_groq_json(messages: List[Dict], model: str, max_tokens: int) -> str:
    client = _groq_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or "{}"


# ─── Model resolution per provider/kind ──────────────────────────────────────

def _model_for(provider: str, kind: str) -> str:
    """kind: 'agent' | 'vision' | 'eval'"""
    table = {
        "openai": {
            "agent": config.openai_agent_model,
            "vision": config.openai_vision_model,
            "eval": config.openai_eval_model,
        },
        "groq": {
            "agent": config.groq_agent_model,
            "vision": config.groq_vision_model,
            "eval": config.groq_eval_model,
        },
    }
    return table[provider][kind]


class LLMClient:
    """
    Fixed-priority router: OpenAI is always tried first.
    Groq is used only when OpenAI raises (missing key, auth failure,
    rate limit, timeout, or any other exception).
    """

    def chat(
        self,
        messages: List[Dict],
        max_tokens: int = 800,
        temperature: float = 0.7,
        kind: str = "agent",
    ) -> str:
        try:
            model = _model_for("openai", kind)
            return _call_openai_chat(messages, model, max_tokens, temperature)
        except Exception as e:
            logger.warning(f"OpenAI chat failed ({e}); attempting Groq fallback.")

        try:
            model = _model_for("groq", kind)
            result = _call_groq_chat(messages, model, max_tokens, temperature)
            logger.info("Groq fallback succeeded for chat completion.")
            return result
        except Exception as e:
            raise LLMError(f"OpenAI failed and Groq fallback also failed: {e}")

    def chat_json(
        self,
        messages: List[Dict],
        max_tokens: int = 300,
        kind: str = "eval",
    ) -> str:
        """Same as chat() but requests a JSON object response. Used by eval_service judge calls."""
        try:
            model = _model_for("openai", kind)
            return _call_openai_json(messages, model, max_tokens)
        except Exception as e:
            logger.warning(f"OpenAI JSON call failed ({e}); attempting Groq fallback.")

        try:
            model = _model_for("groq", kind)
            result = _call_groq_json(messages, model, max_tokens)
            logger.info("Groq fallback succeeded for JSON completion.")
            return result
        except Exception as e:
            raise LLMError(f"OpenAI failed and Groq JSON fallback also failed: {e}")

    def vision(
        self,
        image_b64: str,
        prompt: str,
        max_tokens: int = 1200,
        kind: str = "vision",
    ) -> str:
        try:
            model = _model_for("openai", kind)
            return _call_openai_vision(image_b64, prompt, model, max_tokens)
        except Exception as e:
            logger.warning(f"OpenAI vision failed ({e}); attempting Groq vision fallback.")

        try:
            model = _model_for("groq", kind)
            result = _call_groq_vision(image_b64, prompt, model, max_tokens)
            logger.info("Groq fallback succeeded for vision call.")
            return result
        except Exception as e:
            # Vision is best-effort in the pipeline — don't crash the whole request.
            logger.error(f"Both OpenAI and Groq vision failed: {e}")
            return ""


_client_singleton: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = LLMClient()
        has_openai = bool(config.openai_api_key)
        has_groq = bool(config.groq_api_key)
        logger.info(
            f"LLM client ready. OpenAI configured: {has_openai} (primary) | "
            f"Groq configured: {has_groq} (fallback)."
        )
        if not has_openai and not has_groq:
            logger.error("Neither OPENAI_API_KEY nor GROQ_API_KEY is set. All LLM calls will fail.")
    return _client_singleton
