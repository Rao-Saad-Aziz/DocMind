---
title: Cortex DocMind
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app/demo.py
pinned: false
---

# Cortex DocMind

Ask company documents a question and get a cited answer, only from documents your role may open.

Pipeline: **ingest -> retrieve -> answer -> evaluate**

## Setup
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# install Ollama (ollama.com) and run once:  ollama pull llama3.2
```

## Run order
1. Put 20-40 **public** PDFs in `data/docs/` and describe them in `data/docs/metadata.json`
   (`department`, `access`: public / internal / confidential).
2. Write `data/eval/questions.csv` (columns: question, doc, page, answerable, split dev/test).
3. Try chunk sizes in `notebooks/chunking_experiments.ipynb`, set `CHUNK_SIZE` in `.env`.
4. `python -m src.index` embeds the chunks and saves them locally in `data/index/`.
5. `python -m src.evaluate dev` to tune, then `python -m src.evaluate test` to report.
6. `python -m tests.leak_test` proves an intern never gets a confidential answer.
7. `streamlit run app/demo.py` for the app, `uvicorn api.main:app --reload` for the API (`/docs`).

## Results (test split)
| Method | Recall@5 | MRR |
|---|---|---|
| BM25 keyword | | |
| Vector search | | |
| Vector + rerank | | |

Faithfulness: _ | Refusal on unanswerable: _ | Leaks: 0

## Deploy (Hugging Face Spaces)
1. Create a Space: SDK **Streamlit**, hardware CPU basic (free).
2. Push this repo to the Space (public documents only; `data/index/` is rebuilt on first start).
3. Space -> Settings -> Variables and secrets, add as **secrets**: `LLM_API_KEY` (free key from console.groq.com),
   `UPLOAD_PASSWORD`. Optional variable: `LLM_MODEL`.
4. The first start downloads the embedding models and indexes `data/docs/` (a few minutes).
Uploads made in a free Space are lost when it restarts, so keep your real documents in `data/docs/`.

## Known limits
- Scanned PDFs are flagged, not OCR'd.
- BM25 ignores stop words poorly, so the LLM does the final "not found" check.
- The API trusts the `role` field; a real deployment must take it from a login.
