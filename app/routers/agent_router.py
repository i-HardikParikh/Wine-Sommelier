import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.middleware.auth_dep import get_authenticated_user
from app.models.database import get_db
from app.models.db_models import User
from app.models.schemas import (
    ChatRequest, ChatResponse, IngestResponse,
    ConversationHistory,
)
from app.services.agentic_rag_service import run_query, ingest_document
from app.services.conversation_service import (
    get_or_create_session,
    get_conversation_history,
    save_message,
    update_conversation_title,
    get_user_conversations,
    delete_conversation,
)

router = APIRouter(prefix="/chat", tags=["Chat & RAG"])
ingest_router = APIRouter(prefix="/ingest", tags=["Document Ingestion"])

ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.presentationml.presentation"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/query", response_model=ChatResponse, summary="Ask the wine sommelier")
def query_chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    # Get or create conversation session
    conv = get_or_create_session(db, current_user.id, req.session_id)

    # Retrieve memory (conversation history)
    history = get_conversation_history(db, conv.session_id, current_user.id)

    # Run agentic RAG pipeline
    result = run_query(
        question=req.question,
        conversation_history=history,
        query_type=req.query_type,
    )

    # Save user message + assistant response to DB
    save_message(db, conv.id, "user", req.question)
    save_message(
        db, conv.id, "assistant", result["answer"],
        sources=result["sources"],
        pipeline_path=[str(p) for p in result["pipeline_path"]],
        latency_ms=result["latency_ms"],
    )
    update_conversation_title(db, conv, req.question)

    return ChatResponse(
        answer=result["answer"],
        session_id=conv.session_id,
        sources=result["sources"],
        pipeline_path=[str(p) for p in result["pipeline_path"]],
        latency_ms=result["latency_ms"],
        query_type=result["query_type"],
    )


@router.get("/sessions", response_model=list[ConversationHistory], summary="List all user conversations")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    return get_user_conversations(db, current_user.id)


@router.delete("/sessions/{session_id}", summary="Delete a conversation")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    success = delete_conversation(db, session_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"status": "deleted", "session_id": session_id}


@ingest_router.post("/document", response_model=IngestResponse, summary="Upload and index a wine document")
async def ingest_doc(
    file: UploadFile = File(...),
    current_user: User = Depends(get_authenticated_user),
):
    if file.content_type not in ALLOWED_TYPES and not file.filename.lower().endswith((".pdf", ".pptx")):
        raise HTTPException(status_code=400, detail="Only PDF and PPTX files are supported.")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")

    result = await ingest_document(file_bytes, file.filename)
    return IngestResponse(**result)
