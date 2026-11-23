"""Milestones 2-4: keyword search, vector search, reranking. Every search is filtered by role."""
import re
from functools import lru_cache
from rank_bm25 import BM25Okapi
from src.config import embedder, reranker
from src.index import load


def tokens(text):
    return re.findall(r"\w+", text.lower())


def visible(role):
    """Permission filter: keep ONLY the chunks (and their vectors) this role may see.
    Every search below starts from this, so a forbidden chunk is never even scored."""
    chunks, vectors = load()
    idx = [i for i, c in enumerate(chunks) if role in c["allowed_roles"]]
    return [chunks[i] for i in idx], vectors[idx]


@lru_cache
def _bm25(role):
    docs, _ = visible(role)
    return docs, (BM25Okapi([tokens(d["text"]) for d in docs]) if docs else None)


def refresh():
    """Call after uploading a document so searches see it."""
    _bm25.cache_clear()
    load.cache_clear()


def bm25_search(question, role, k=20):
    docs, bm25 = _bm25(role)
    if not docs:
        return []
    scores = bm25.get_scores(tokens(question))
    best = sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)[:k]
    return [docs[i] for i in best if scores[i] > 0]


def vector_search(question, role, k=20):
    docs, vectors = visible(role)
    if not docs:
        return []
    q = embedder().encode(question, normalize_embeddings=True)
    scores = vectors @ q                        # cosine similarity (vectors are normalized)
    best = scores.argsort()[::-1][:k]
    return [docs[i] for i in best]


def rerank(question, chunks, k=5):
    """A cross-encoder reads question + chunk together: slower but more accurate than vectors."""
    if not chunks:
        return []
    scores = reranker().predict([(question, c["text"]) for c in chunks])
    ranked = sorted(zip(scores, chunks), key=lambda pair: pair[0], reverse=True)
    return [c for _, c in ranked][:k]


def search(question, role, mode="rerank", k=5):
    """mode: 'bm25' | 'vector' | 'rerank' (vector top 20, then cross-encoder)."""
    if mode == "bm25":
        return bm25_search(question, role, k)
    if mode == "vector":
        return vector_search(question, role, k)
    return rerank(question, vector_search(question, role, 20), k)
