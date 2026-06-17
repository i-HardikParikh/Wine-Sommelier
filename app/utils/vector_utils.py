import time
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from loguru import logger

from app.models.config import get_config

config = get_config()
_pinecone: Optional[Pinecone] = None
_index = None
_openai_embed_client = None


def _get_openai_embed_client():
    """
    Embeddings are OpenAI-only: Groq has no embeddings API, so there is no
    fallback provider here. If OPENAI_API_KEY is missing or invalid, ingestion
    and retrieval will fail with a clear error rather than silently degrading.
    """
    global _openai_embed_client
    if _openai_embed_client is None:
        if not config.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required for embeddings (Pinecone vector search). "
                "Groq does not provide an embeddings API, so there is no fallback for this step."
            )
        from openai import OpenAI
        _openai_embed_client = OpenAI(api_key=config.openai_api_key)
    return _openai_embed_client


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Batch embed texts using OpenAI (no fallback provider available)."""
    client = _get_openai_embed_client()
    response = client.embeddings.create(model=config.embedding_model, input=texts)
    return [r.embedding for r in response.data]


def get_pinecone_index():
    global _pinecone, _index
    if _index is not None:
        return _index

    _pinecone = Pinecone(api_key=config.pinecone_api_key)
    existing = [i.name for i in _pinecone.list_indexes()]

    if config.pinecone_index_name not in existing:
        logger.info(f"Creating Pinecone index: {config.pinecone_index_name}")
        _pinecone.create_index(
            name=config.pinecone_index_name,
            dimension=config.embedding_dimensions,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=config.pinecone_environment.replace("-aws", "")),
        )
        while not _pinecone.describe_index(config.pinecone_index_name).status["ready"]:
            time.sleep(1)

    _index = _pinecone.Index(config.pinecone_index_name)
    logger.info(f"Pinecone index ready (dim={config.embedding_dimensions}, embedding model={config.embedding_model}).")
    return _index


def upsert_chunks(chunks: List[Dict[str, Any]]) -> int:
    """
    Upsert document chunks into Pinecone.
    Each chunk: {"id": str, "text": str, "metadata": dict}
    Returns number of vectors upserted.
    """
    index = get_pinecone_index()
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    vectors = [
        {
            "id": chunk["id"],
            "values": embedding,
            "metadata": {**chunk.get("metadata", {}), "text": chunk["text"]},
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]

    batch_size = 100
    total = 0
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        index.upsert(vectors=batch)
        total += len(batch)

    logger.info(f"Upserted {total} vectors to Pinecone.")
    return total


def query_vectors(
    query_text: str,
    top_k: int = None,
    filter: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """
    Query Pinecone for similar chunks.
    Returns list of matches with text + metadata.
    """
    index = get_pinecone_index()
    top_k = top_k or config.top_k_results
    [embedding] = embed_texts([query_text])

    response = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter,
    )

    results = []
    for match in response.matches:
        results.append({
            "id": match.id,
            "score": match.score,
            "text": match.metadata.get("text", ""),
            "source": match.metadata.get("source", "unknown"),
            "page": match.metadata.get("page", 0),
            "chunk_type": match.metadata.get("chunk_type", "text"),
        })

    return results
