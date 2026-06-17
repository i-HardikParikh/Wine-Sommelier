import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict

from sqlalchemy.orm import Session
from loguru import logger

from app.models.db_models import Conversation, Message
from app.models.schemas import ChatMessage, ConversationHistory


def get_or_create_session(db: Session, user_id: int, session_id: Optional[str] = None) -> Conversation:
    """Get existing conversation or create a new one."""
    if session_id:
        conv = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == user_id,
        ).first()
        if conv:
            return conv

    # Create new session
    new_session_id = session_id or str(uuid.uuid4())
    conv = Conversation(
        session_id=new_session_id,
        user_id=user_id,
        title="New Conversation",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation_history(db: Session, session_id: str, user_id: int) -> List[Dict]:
    """Return the last N messages as [{role, content}] dicts for LLM context."""
    conv = db.query(Conversation).filter(
        Conversation.session_id == session_id,
        Conversation.user_id == user_id,
    ).first()
    if not conv:
        return []

    messages = db.query(Message).filter(
        Message.conversation_id == conv.id
    ).order_by(Message.timestamp).all()

    return [{"role": m.role, "content": m.content} for m in messages]


def save_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    sources: List[str] = None,
    pipeline_path: List[str] = None,
    latency_ms: float = 0.0,
) -> Message:
    """Persist a single message to the database."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=json.dumps(sources or []),
        pipeline_path=json.dumps(pipeline_path or []),
        latency_ms=latency_ms,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def update_conversation_title(db: Session, conv: Conversation, question: str):
    """Auto-generate a title from the first user message."""
    if conv.title == "New Conversation" and question:
        conv.title = question[:50] + ("..." if len(question) > 50 else "")
        conv.updated_at = datetime.utcnow()
        db.commit()


def get_user_conversations(db: Session, user_id: int) -> List[ConversationHistory]:
    """List all conversations for a user."""
    convs = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.updated_at.desc()).all()

    results = []
    for conv in convs:
        messages = db.query(Message).filter(Message.conversation_id == conv.id).all()
        chat_messages = [
            ChatMessage(
                role=m.role,
                content=m.content,
                timestamp=m.timestamp,
                sources=json.loads(m.sources or "[]"),
            )
            for m in messages
        ]
        results.append(ConversationHistory(
            session_id=conv.session_id,
            messages=chat_messages,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        ))
    return results


def delete_conversation(db: Session, session_id: str, user_id: int) -> bool:
    """Delete a conversation and all its messages."""
    conv = db.query(Conversation).filter(
        Conversation.session_id == session_id,
        Conversation.user_id == user_id,
    ).first()
    if not conv:
        return False
    db.delete(conv)
    db.commit()
    return True
