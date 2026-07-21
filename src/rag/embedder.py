"""
Atlas AI — RAG Embedder
Builds a FAISS vector index from GOV.UK immigration guidance chunks.
Uses sentence-transformers/all-MiniLM-L6-v2 for efficient CPU embedding.
"""

import json
import pickle
from pathlib import Path
from typing import Optional

from config import EMBEDDINGS_INDEX_PATH, EMBEDDING_MODEL
from src.rag.gov_uk_loader import get_govuk_documents, DocumentChunk

# Lazy-loaded model and index
_embed_model = None
_faiss_index = None
_doc_chunks: list[DocumentChunk] = []


def _load_embed_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embed_model


def _get_index_path() -> Path:
    return EMBEDDINGS_INDEX_PATH


def build_index(force_rebuild: bool = False) -> None:
    """
    Build and persist the FAISS vector index.
    Only rebuilds if index doesn't exist or force_rebuild=True.
    """
    import faiss
    import numpy as np

    index_path = _get_index_path()
    index_file = index_path / "index.faiss"
    chunks_file = index_path / "chunks.pkl"

    if index_file.exists() and chunks_file.exists() and not force_rebuild:
        print("[RAG] Index already exists. Skipping rebuild.")
        return

    print("[RAG] Building FAISS index from GOV.UK documents...")
    index_path.mkdir(parents=True, exist_ok=True)

    model = _load_embed_model()
    chunks = get_govuk_documents()

    texts = [c.text for c in chunks]
    print(f"[RAG] Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    embeddings = embeddings.astype("float32")

    # Normalise for cosine similarity
    import numpy as np
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings_norm = embeddings / (norms + 1e-10)

    # Build flat L2 index (cosine sim via normalised vectors)
    dimension = embeddings_norm.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product = cosine sim for normalised vectors
    index.add(embeddings_norm)

    # Persist
    faiss.write_index(index, str(index_file))
    with open(chunks_file, "wb") as f:
        pickle.dump(chunks, f)

    print(f"[RAG] Index built: {index.ntotal} vectors, dim={dimension}")
    print(f"[RAG] Saved to {index_path}")


def load_index() -> tuple:
    """Load the FAISS index and doc chunks from disk."""
    global _faiss_index, _doc_chunks
    if _faiss_index is not None:
        return _faiss_index, _doc_chunks

    import faiss

    index_path = _get_index_path()
    index_file = index_path / "index.faiss"
    chunks_file = index_path / "chunks.pkl"

    if not index_file.exists() or not chunks_file.exists():
        print("[RAG] Index not found. Building now...")
        build_index()

    _faiss_index = faiss.read_index(str(index_file))
    with open(chunks_file, "rb") as f:
        _doc_chunks = pickle.load(f)

    print(f"[RAG] Loaded index: {_faiss_index.ntotal} vectors")
    return _faiss_index, _doc_chunks
