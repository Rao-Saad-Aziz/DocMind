"""Settings and shared helpers. Models are loaded lazily so importing this file is cheap."""
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # 384-dim vectors
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 200))            # words per chunk
OVERLAP = int(os.getenv("OVERLAP", 30))                   # words shared between chunks

DOCS_DIR = "data/docs"
INDEX_DIR = "data/index"        # chunks and vectors are saved here (local, no database)
QUESTIONS = "data/eval/questions.csv"

ROLES = ["intern", "staff", "hr", "admin"]
# access level -> roles allowed to read it
ACCESS = {
    "public": ["intern", "staff", "hr", "admin"],
    "internal": ["staff", "hr", "admin"],
    "confidential": ["hr", "admin"],
}


@lru_cache
def embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)


@lru_cache
def reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder(RERANK_MODEL)