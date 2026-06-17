import time
from typing import List, Optional

from loguru import logger

from app.agent.agent_graph import wine_agent
from app.agent.document_processing import load_document
from app.models.enums import QueryType
from app.utils.chunking_utils import chunk_documents
from app.utils.vector_utils import upsert_chunks


async def ingest_document(file_bytes: bytes, filename: str) -> dict:
    """
    Full ingestion pipeline:
    1. Load and parse PDF/PPTX
    2. Chunk text sections
    3. Upsert to Pinecone
    Returns stats dict.
    """
    t0 = time.time()
    logger.info(f"Starting ingestion: {filename}")

    raw_docs = load_document(file_bytes, filename)
    chunks = chunk_documents(raw_docs)

    images_processed = sum(1 for d in raw_docs if d.get("chunk_type") in ("vision", "ocr"))
    total_upserted = upsert_chunks(chunks)

    elapsed = (time.time() - t0) * 1000
    logger.info(f"Ingestion complete: {total_upserted} chunks in {elapsed:.0f}ms")

    return {
        "filename": filename,
        "status": "processed",
        "chunks_indexed": total_upserted,
        "images_processed": images_processed,
        "processing_time_ms": round(elapsed, 1),
    }


def run_query(
    question: str,
    conversation_history: Optional[List[dict]] = None,
    query_type: Optional[QueryType] = None,
) -> dict:
    """
    Run the full agentic RAG pipeline for a question.
    Returns answer, sources, pipeline_path, latency_ms, query_type.
    """
    t0 = time.time()

    initial_state = {
        "question": question,
        "query_type": query_type or QueryType.GENERAL,
        "conversation_history": conversation_history or [],
        "vector_results": [],
        "vision_result": "",
        "ocr_result": "",
        "answer": "",
        "sources": [],
        "pipeline_path": [],
        "context_sufficient": False,
        "start_time": t0,
    }

    final_state = wine_agent.invoke(initial_state)
    elapsed = (time.time() - t0) * 1000

    return {
        "answer": final_state["answer"],
        "sources": final_state.get("sources", []),
        "pipeline_path": final_state.get("pipeline_path", []),
        "latency_ms": round(elapsed, 1),
        "query_type": final_state.get("query_type", QueryType.GENERAL),
    }
