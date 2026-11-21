"""Settings and shared helpers. Models are loaded lazily so importing this file is cheap."""
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

# On Streamlit Community Cloud the keys live in "Secrets", not in .env: copy them into the environment.
try:
    import streamlit as st
    for _k in ("LLM_API_KEY", "UPLOAD_PASSWORD", "LLM_MODEL"):
        if _k not in os.environ and _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass                                   # no Streamlit or no secrets: just use .env / environment

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # 384-dim vectors
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
# No LLM_API_KEY -> free local Ollama model. With LLM_API_KEY -> hosted OpenAI-compatible API (default: Groq, free tier).
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile" if LLM_API_KEY else "llama3.2")
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
