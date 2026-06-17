import uuid
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.models.config import get_config

config = get_config()


def chunk_text(
    text: str,
    source: str,
    page: int = 0,
    chunk_type: str = "text",
    extra_metadata: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks suitable for vector indexing.
    Returns a list of chunk dicts ready for upsert_chunks().
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    pieces = splitter.split_text(text)

    chunks = []
    for i, piece in enumerate(pieces):
        if not piece.strip():
            continue
        metadata = {
            "source": source,
            "page": page,
            "chunk_index": i,
            "chunk_type": chunk_type,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        chunks.append({
            "id": str(uuid.uuid4()),
            "text": piece.strip(),
            "metadata": metadata,
        })

    return chunks


def chunk_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of {text, source, page, chunk_type, metadata} dicts
    and return all flattened chunks ready for Pinecone.
    """
    all_chunks = []
    for doc in documents:
        chunks = chunk_text(
            text=doc["text"],
            source=doc.get("source", "unknown"),
            page=doc.get("page", 0),
            chunk_type=doc.get("chunk_type", "text"),
            extra_metadata=doc.get("metadata"),
        )
        all_chunks.extend(chunks)
    return all_chunks
