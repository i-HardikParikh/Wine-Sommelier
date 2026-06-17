from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.enums import QueryType, EvalMetric


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserPublic"


class UserPublic(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Chat / RAG Schemas ──────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: Optional[datetime] = None
    sources: Optional[List[str]] = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    query_type: Optional[QueryType] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: List[str] = []
    pipeline_path: List[str] = []
    latency_ms: float
    query_type: QueryType


class ConversationHistory(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime


# ─── Ingestion Schemas ───────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    filename: str
    status: str
    chunks_indexed: int
    images_processed: int
    processing_time_ms: float


class IngestStatusResponse(BaseModel):
    task_id: str
    status: str  # "pending" | "processing" | "done" | "failed"
    progress: int  # 0-100
    result: Optional[IngestResponse] = None
    error: Optional[str] = None


# ─── Eval Schemas ────────────────────────────────────────────────────────────

class EvalSample(BaseModel):
    question: str
    expected_answer: Optional[str] = None
    context: Optional[str] = None


class EvalRunRequest(BaseModel):
    num_samples: int = Field(default=10, ge=1, le=100)
    custom_samples: Optional[List[EvalSample]] = None


class EvalScore(BaseModel):
    metric: EvalMetric
    score: float  # 0.0 – 1.0
    reasoning: str


class EvalResult(BaseModel):
    sample_id: str
    question: str
    answer: str
    scores: List[EvalScore]
    overall_score: float
    evaluated_at: datetime


class EvalRunResponse(BaseModel):
    run_id: str
    status: str
    num_samples: int
    results: List[EvalResult] = []
    aggregate_scores: Dict[str, float] = {}
    started_at: datetime
    completed_at: Optional[datetime] = None


# ─── Health Schemas ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]
    uptime_seconds: float
