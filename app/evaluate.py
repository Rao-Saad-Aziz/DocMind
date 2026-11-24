"""Score the search with Recall@5 and MRR.  Usage (from the project folder):  python app/evaluate.py dev|test
Needs data/eval/questions.csv with columns: question, doc, page, answerable, split"""
import sys, csv, json, time
import core

split = sys.argv[1] if len(sys.argv) > 1 else "dev"
core.seed()
rows = [r for r in csv.DictReader(open("data/eval/questions.csv", encoding="utf-8"))
        if r["split"] == split and r["answerable"] == "yes"]

ranks = []
for r in rows:
    found = core.search(r["question"], "admin", 10)       # admin sees every document
    ranks.append(next((i + 1 for i, c in enumerate(found)
                       if c["doc"] == r["doc"] and c["page"] <= int(r["page"]) <= c["page_end"]), 0))

recall = sum(1 for x in ranks if 0 < x <= 5) / len(ranks)
mrr = sum(1 / x for x in ranks if x) / len(ranks)
print(f"{split}: {len(rows)} questions | BM25 Recall@5 = {recall:.3f} | MRR = {mrr:.3f}")
for r, x in zip(rows, ranks):
    if not 0 < x <= 5:
        print("  MISSED:", r["question"])
with open("data/eval/runs.jsonl", "a") as f:               # log every run
    f.write(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M"), "split": split, "method": "bm25",
                        "recall@5": round(recall, 3), "mrr": round(mrr, 3)}) + "\n")
