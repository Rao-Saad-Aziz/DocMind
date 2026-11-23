"""Milestone 4: FastAPI endpoint.  Run: uvicorn api.main:app --reload   then open /docs"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.config import ROLES
from src.retrieve import search
from src.answer import answer

app = FastAPI(title="Cortex DocMind")


class Question(BaseModel):
    question: str
    role: str = "intern"      # demo only: a real app would take the role from the user's login


@app.post("/ask")
def ask(body: Question):
    if body.role not in ROLES:
        raise HTTPException(400, f"role must be one of {ROLES}")
    chunks = search(body.question, body.role, "rerank", 5)
    return {"answer": answer(body.question, chunks),
            "sources": [{"doc": c["doc"], "page": c["page"], "text": c["text"]} for c in chunks]}
