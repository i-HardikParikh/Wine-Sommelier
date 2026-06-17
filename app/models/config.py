from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Union
from pydantic import field_validator



# Configuration models
class WineRAGConfig(BaseSettings):
    # ─── OpenAI (PRIMARY) ────────────────────────────────────────────────────
    # Always tried first for every LLM call (chat, vision, eval) and is the
    # ONLY provider used for embeddings (Groq has no embeddings API).
    openai_api_key: str = ""
    openai_agent_model: str = "gpt-4o-mini"
    openai_vision_model: str = "gpt-4o"
    openai_eval_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072

    # ─── Groq (FALLBACK — chat & vision only, not embeddings) ───────────────
    # Used automatically when an OpenAI call fails (missing key, auth error,
    # rate limit, timeout, 5xx, etc). Leave blank to disable fallback.
    groq_api_key: str = ""
    groq_agent_model: str = "llama-3.3-70b-versatile"
    groq_vision_model: str = "llama-4-scout-17b-16e-instruct"
    groq_eval_model: str = "llama-3.3-70b-versatile"

    # ─── Pinecone ────────────────────────────────────────────────────────────
    pinecone_api_key: str
    pinecone_environment: str = "us-east-1-aws"
    pinecone_index_name: str = "wine-knowledge"

    # ─── JWT Auth ────────────────────────────────────────────────────────────
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # ─── Database ────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./wine_sommelier.db"

    # ─── App ─────────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


    # ─── Chunking ────────────────────────────────────────────────────────────
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_config() -> WineRAGConfig:
    return WineRAGConfig()
