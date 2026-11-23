"""Milestone 3: embed chunks and save them (text + vector + permissions) in local files.
Usage: python -m src.index        (re-indexes everything in data/docs)"""
import os, json
from functools import lru_cache
import numpy as np
from src.config import embedder, DOCS_DIR, INDEX_DIR
from src.ingest import ingest_file, load_all, load_meta

CHUNKS_FILE = os.path.join(INDEX_DIR, "chunks.json")    # text + page + doc + allowed_roles
VECTORS_FILE = os.path.join(INDEX_DIR, "vectors.npy")   # one 384-number vector per chunk, same order


@lru_cache
def load():
    """Return (chunks, vectors). Empty if nothing has been indexed yet."""
    if not os.path.exists(CHUNKS_FILE):
        return [], np.zeros((0, 384))
    return json.load(open(CHUNKS_FILE, encoding="utf-8")), np.load(VECTORS_FILE)


def save(chunks, vectors):
    os.makedirs(INDEX_DIR, exist_ok=True)
    json.dump(chunks, open(CHUNKS_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    np.save(VECTORS_FILE, vectors)
    load.cache_clear()


def embed(chunks):
    return embedder().encode([c["text"] for c in chunks], normalize_embeddings=True)


def add_document(path, department="general", access="internal"):
    """Used by the Streamlit upload: (re)index one file and remember its metadata."""
    name = os.path.basename(path)
    meta = load_meta()
    meta[name] = {"department": department, "access": access}
    json.dump(meta, open(os.path.join(DOCS_DIR, "metadata.json"), "w"), indent=2)

    new, empty = ingest_file(path, department, access)
    old, old_vecs = load()
    keep = [i for i, c in enumerate(old) if c["doc"] != name]      # drop the old copy of this file
    chunks = [old[i] for i in keep] + new
    vectors = np.vstack([old_vecs[keep], embed(new)]) if new else old_vecs[keep]
    save(chunks, vectors)
    return len(new), empty


def ensure_index():
    """On a fresh server (no data/index yet) build the index from the files in data/docs."""
    if load()[0] or not os.path.isdir(DOCS_DIR):
        return
    chunks = load_all()
    if chunks:
        save(chunks, embed(chunks))


if __name__ == "__main__":
    chunks = load_all()
    if not chunks:
        raise SystemExit("No chunks found. Put files in data/docs/ first.")
    save(chunks, embed(chunks))
    print(f"Indexed {len(chunks)} chunks into {INDEX_DIR}/")
