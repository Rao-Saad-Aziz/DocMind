"""Leak test: an intern must never get a chunk or a citation from a confidential document.
Usage: python -m tests.leak_test"""
import pandas as pd
from src.config import QUESTIONS
from src.ingest import load_meta
from src.retrieve import search
from src.answer import answer

secret = {f for f, m in load_meta().items() if m.get("access") == "confidential"}
qs = pd.read_csv(QUESTIONS)
qs = qs[qs.doc.isin(secret)].question           # questions whose answer lives in a confidential file

leaks = 0
for q in qs:
    for mode in ["bm25", "vector", "rerank"]:
        if any(c["doc"] in secret for c in search(q, "intern", mode, 10)):
            leaks += 1
            print(f"LEAK ({mode}): {q}")
    text = answer(q, search(q, "intern", "rerank", 5))
    if any(d in text for d in secret):
        leaks += 1
        print(f"LEAK (answer cites a secret file): {q}")

print(f"{len(qs)} confidential questions asked as intern, {leaks} leaks")
assert leaks == 0, "Permission filter is broken!"
