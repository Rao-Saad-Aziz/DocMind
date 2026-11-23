"""Milestones 2-4: score keyword vs vector vs vector+rerank, then the answer quality.
Usage: python -m src.evaluate dev     (tune on this)
       python -m src.evaluate test    (report this)"""
import sys, json, time
import numpy as np, pandas as pd
from src.config import QUESTIONS, CHUNK_SIZE, OVERLAP, EMBED_MODEL, RERANK_MODEL, LLM_MODEL
from src.retrieve import search
from src.answer import answer, llm, NOT_FOUND

MODES = ["bm25", "vector", "rerank"]
ROLE = "admin"          # sees every document, so retrieval is judged on the documents themselves


def faithful(ans, chunks):
    """LLM judge: is every claim in the answer backed by the retrieved passages?"""
    ctx = "\n\n".join(c["text"] for c in chunks)
    verdict = llm(f"Passages:\n{ctx}\n\nAnswer:\n{ans}\n\n"
                  "Is every claim in the answer supported by the passages? Reply only YES or NO.",
                  "You are a strict grader.")
    return verdict.strip().upper().startswith("YES")


def main(split):
    df = pd.read_csv(QUESTIONS)
    df = df[df.split == split]
    can, cant = df[df.answerable == "yes"], df[df.answerable == "no"]

    rows = []
    for mode in MODES:
        ranks = []
        for q in can.itertuples():
            res = search(q.question, ROLE, mode, 10)
            ranks.append(next((i + 1 for i, c in enumerate(res)
                               if c["doc"] == q.doc and q.page in c["pages"]), 0))   # 0 = not found
        r = np.array(ranks)
        rows.append({"method": mode,
                     "Recall@5": np.mean((r > 0) & (r <= 5)),
                     "MRR": np.mean(np.where(r > 0, 1 / np.maximum(r, 1), 0))})
    table = pd.DataFrame(rows).round(3)

    # Answer quality, using the best retriever (vector + rerank)
    faith = []
    for q in can.itertuples():
        chunks = search(q.question, ROLE, "rerank", 5)
        a = answer(q.question, chunks)
        if a != NOT_FOUND:
            faith.append(faithful(a, chunks))
    refused = [answer(q.question, search(q.question, ROLE, "rerank", 5)) == NOT_FOUND
               for q in cant.itertuples()]
    extra = {"faithfulness": round(float(np.mean(faith)), 3) if faith else None,
             "refusal_on_unanswerable": round(float(np.mean(refused)), 3) if refused else None}

    print(f"\nSplit: {split}  ({len(can)} answerable, {len(cant)} unanswerable)\n")
    print(table.to_string(index=False))
    print("\n", extra)
    table.to_csv(f"data/eval/results_{split}.csv", index=False)

    # Log every run so anyone can repeat it
    with open("data/eval/runs.jsonl", "a") as f:
        f.write(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M"), "split": split,
                            "chunk_size": CHUNK_SIZE, "overlap": OVERLAP, "embed": EMBED_MODEL,
                            "rerank": RERANK_MODEL, "llm": LLM_MODEL,
                            "results": table.to_dict("records"), **extra}) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dev")
