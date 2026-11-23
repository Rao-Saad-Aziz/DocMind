"""Milestone 1: read PDF/Word files, clean them, split into tagged chunks."""
import os, re, json, collections
import pymupdf, docx
from src.config import ACCESS, CHUNK_SIZE, OVERLAP, DOCS_DIR


def load_meta(folder=DOCS_DIR):
    """metadata.json maps file name -> {"department": ..., "access": ...}."""
    path = os.path.join(folder, "metadata.json")
    return json.load(open(path)) if os.path.exists(path) else {}


def read_pages(path):
    """Return [(page_number, text)]. Word files have no pages, so every 3000 characters counts as one."""
    if path.lower().endswith(".pdf"):
        return [(i, p.get_text()) for i, p in enumerate(pymupdf.open(path), 1)]
    text = "\n".join(p.text for p in docx.Document(path).paragraphs)
    return [(i + 1, text[j:j + 3000]) for i, j in enumerate(range(0, len(text), 3000))]


def strip_repeated(pages):
    """Remove headers/footers: short lines (page numbers ignored) that appear on over half the pages."""
    if len(pages) < 3:
        return pages
    norm = lambda line: re.sub(r"\d+", "#", line.strip())
    seen = collections.Counter(n for _, t in pages for n in {norm(l) for l in t.splitlines() if l.strip()})
    common = {n for n, c in seen.items() if c > len(pages) / 2}
    keep = lambda l: not (l.strip() and len(l) < 80 and norm(l) in common)
    return [(n, "\n".join(l for l in t.splitlines() if keep(l))) for n, t in pages]


def is_heading(line):
    """'1.2 Leave Policy' or 'LEAVE POLICY' -> True."""
    line = line.strip()
    return 0 < len(line) < 80 and bool(re.match(r"^(\d+(\.\d+)*[.)]?\s+[A-Z]|[A-Z][A-Z0-9 &/,-]{3,}$)", line))


def chunk(pages, size=CHUNK_SIZE, overlap=OVERLAP):
    """Split by headings; also cut every `size` words, repeating `overlap` words so context is not lost."""
    chunks, buf, fresh = [], [], 0          # buf holds (word, page); fresh = new words since last cut

    def flush(keep_overlap):
        nonlocal buf, fresh
        if fresh:
            new = buf[-fresh:]
            chunks.append({"page": new[0][1], "pages": sorted({p for _, p in new}),
                           "text": " ".join(w for w, _ in buf)})
        buf, fresh = (buf[-overlap:] if keep_overlap else []), 0

    for page, text in pages:
        for line in text.splitlines():
            if is_heading(line):
                flush(False)
            for w in line.split():
                buf.append((w, page))
                fresh += 1
                if len(buf) >= size:
                    flush(True)
    flush(False)
    return chunks


def ingest_file(path, department="general", access="internal", size=CHUNK_SIZE, overlap=OVERLAP):
    """Return (chunks tagged with doc/page/access, list of pages with no text)."""
    pages = strip_repeated(read_pages(path))
    empty = [n for n, t in pages if len(t.strip()) < 20]     # scanned page: no text layer
    name = os.path.basename(path)
    chunks = chunk(pages, size, overlap)
    for c in chunks:
        c.update(doc=name, department=department, access=access, allowed_roles=ACCESS[access])
    return chunks, empty


def load_all(folder=DOCS_DIR, size=CHUNK_SIZE, overlap=OVERLAP):
    meta, out = load_meta(folder), []
    for f in sorted(os.listdir(folder)):
        if f.lower().endswith((".pdf", ".docx")):
            m = meta.get(f, {})
            chunks, empty = ingest_file(os.path.join(folder, f), m.get("department", "general"),
                                        m.get("access", "internal"), size, overlap)
            if empty:
                print(f"WARNING {f}: pages {empty} have no text (scanned? needs OCR)")
            out += chunks
    return out


if __name__ == "__main__":      # python -m src.ingest   -> shows what was read, no database needed
    chunks = load_all()
    print(f"{len(chunks)} chunks from {len({c['doc'] for c in chunks})} documents")
    for c in chunks[:5]:
        print(f"- {c['doc']} p.{c['page']} [{c['access']}] {c['text'][:80]}...")
