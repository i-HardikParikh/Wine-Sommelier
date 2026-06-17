import time
from typing import TypedDict, List, Optional, Annotated
import operator

from loguru import logger

from app.models.config import get_config
from app.models.enums import QueryType, NodeType
from app.utils.vector_utils import query_vectors
from app.utils.llm_client import get_llm_client

config = get_config()
_llm = get_llm_client()

# ─── State Definition ────────────────────────────────────────────────────────

class AgentState(TypedDict):
    question: str
    query_type: QueryType
    conversation_history: List[dict]          # [{role, content}, ...]
    vector_results: List[dict]                # Pinecone matches
    vision_result: str
    ocr_result: str
    answer: str
    sources: List[str]
    pipeline_path: Annotated[List[str], operator.add]
    context_sufficient: bool
    start_time: float


# ─── Node: analyze_query ─────────────────────────────────────────────────────

def analyze_query(state: AgentState) -> AgentState:
    """Classify the query type and prepare it for retrieval."""
    t0 = time.time()
    question = state["question"]

    raw = _llm.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a wine query classifier. Classify the user's question into one of: "
                    "wine_pairing, wine_recommendation, wine_education, cellar_management, general. "
                    "Reply with ONLY the category name, nothing else."
                ),
            },
            {"role": "user", "content": question},
        ],
        max_tokens=20,
        temperature=0,
    ).strip().lower()

    try:
        query_type = QueryType(raw)
    except ValueError:
        query_type = QueryType.GENERAL

    logger.info(f"[analyze_query] classified as '{query_type}' in {(time.time()-t0)*1000:.0f}ms")
    return {**state, "query_type": query_type, "pipeline_path": [NodeType.ANALYZE_QUERY]}


# ─── Node: vector_search ─────────────────────────────────────────────────────

def vector_search(state: AgentState) -> AgentState:
    """Query Pinecone for semantically similar chunks."""
    t0 = time.time()
    results = query_vectors(state["question"], top_k=config.top_k_results)
    logger.info(f"[vector_search] {len(results)} results in {(time.time()-t0)*1000:.0f}ms")
    return {**state, "vector_results": results, "pipeline_path": [NodeType.VECTOR_SEARCH]}


# ─── Node: vision_analysis ───────────────────────────────────────────────────

def vision_analysis(state: AgentState) -> AgentState:
    """
    Retrieve image-based vector chunks (chunk_type == 'vision')
    and summarise them for the question.
    """
    t0 = time.time()
    vision_chunks = [r for r in state["vector_results"] if r.get("chunk_type") == "vision"]

    if not vision_chunks:
        logger.info("[vision_analysis] no vision chunks found")
        return {**state, "vision_result": "", "pipeline_path": [NodeType.VISION_ANALYSIS]}

    context = "\n\n".join(c["text"] for c in vision_chunks[:3])
    result = _llm.chat(
        messages=[
            {"role": "system", "content": "You are an expert wine sommelier. Answer based on the visual data provided."},
            {"role": "user", "content": f"Context from wine images:\n{context}\n\nQuestion: {state['question']}"},
        ],
        max_tokens=600,
    )
    logger.info(f"[vision_analysis] done in {(time.time()-t0)*1000:.0f}ms")
    return {**state, "vision_result": result, "pipeline_path": [NodeType.VISION_ANALYSIS]}


# ─── Node: ocr_analysis ──────────────────────────────────────────────────────

def ocr_analysis(state: AgentState) -> AgentState:
    """Use OCR-derived chunks as additional context."""
    t0 = time.time()
    ocr_chunks = [r for r in state["vector_results"] if r.get("chunk_type") == "ocr"]

    if not ocr_chunks:
        logger.info("[ocr_analysis] no OCR chunks found")
        return {**state, "ocr_result": "", "pipeline_path": [NodeType.OCR_ANALYSIS]}

    context = "\n\n".join(c["text"] for c in ocr_chunks[:3])
    result = _llm.chat(
        messages=[
            {"role": "system", "content": "You are an expert wine sommelier. Use the OCR-extracted text to answer."},
            {"role": "user", "content": f"OCR text:\n{context}\n\nQuestion: {state['question']}"},
        ],
        max_tokens=400,
    )
    logger.info(f"[ocr_analysis] done in {(time.time()-t0)*1000:.0f}ms")
    return {**state, "ocr_result": result, "pipeline_path": [NodeType.OCR_ANALYSIS]}


# ─── Node: answer_synthesis ──────────────────────────────────────────────────

SOMMELIER_SYSTEM = """You are an elegant, knowledgeable personal wine sommelier with decades of experience.
Your role is to:
- Give warm, confident, expert wine advice
- Reference specific wines, regions, and vintages when appropriate
- Suggest food pairings naturally
- Use elegant but accessible language — not pretentious
- Draw primarily from the provided context, then your own expertise

If context is provided, cite it naturally. If no context, use your expert knowledge.
Always end with a concise, memorable recommendation or insight."""


def answer_synthesis(state: AgentState) -> AgentState:
    """Synthesise a final answer from all retrieved context + conversation history."""
    t0 = time.time()

    context_parts = []
    text_chunks = [r for r in state["vector_results"] if r.get("chunk_type") == "text"]
    if text_chunks:
        context_parts.append("Retrieved wine knowledge:\n" + "\n\n".join(c["text"] for c in text_chunks[:4]))
    if state.get("vision_result"):
        context_parts.append("Visual wine data:\n" + state["vision_result"])
    if state.get("ocr_result"):
        context_parts.append("Scanned text:\n" + state["ocr_result"])

    context_str = "\n\n---\n\n".join(context_parts) if context_parts else ""
    context_sufficient = bool(context_str.strip())

    messages = [{"role": "system", "content": SOMMELIER_SYSTEM}]
    for msg in state.get("conversation_history", [])[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = f"{f'Context:' + chr(10) + context_str + chr(10)*2 if context_str else ''}Question: {state['question']}"
    messages.append({"role": "user", "content": user_content})

    answer = _llm.chat(messages=messages, max_tokens=800, temperature=0.7)
    sources = list({r["source"] for r in state["vector_results"] if r.get("source")})

    logger.info(f"[answer_synthesis] done in {(time.time()-t0)*1000:.0f}ms")
    return {
        **state,
        "answer": answer,
        "sources": sources,
        "context_sufficient": context_sufficient,
        "pipeline_path": [NodeType.ANSWER_SYNTHESIS],
    }


# ─── Node: fallback ──────────────────────────────────────────────────────────

def fallback(state: AgentState) -> AgentState:
    """Pure LLM fallback when no context was found in the knowledge base."""
    t0 = time.time()
    messages = [
        {"role": "system", "content": SOMMELIER_SYSTEM + "\n\nNote: No documents have been ingested yet. Use your expert wine knowledge to answer."},
    ]
    for msg in state.get("conversation_history", [])[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": state["question"]})

    answer = _llm.chat(messages=messages, max_tokens=700, temperature=0.7)
    logger.info(f"[fallback] done in {(time.time()-t0)*1000:.0f}ms")
    return {**state, "answer": answer, "sources": [], "pipeline_path": [NodeType.FALLBACK]}
