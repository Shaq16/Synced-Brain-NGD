"""
main.py — Synced Brain FastAPI application.

Endpoints:
  GET  /health  — liveness probe
  POST /query   — RAG query against Milvus + Gemini answer generation
"""
import os
from contextlib import asynccontextmanager
from typing import Optional

import cohere
from google import genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.vectorstore.milvus_store import get_or_create_collection, search

# for immediate prototyping
from groq import Groq

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# immediate prototyping
GROQ_API_KEY = os.getenv("GROQ_API_KEY","")

ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")
EMBED_MODEL = "embed-english-v3.0"



_collection = None   # lazy-loaded singleton


def get_col():
    global _collection
    if _collection is None:
        _collection = get_or_create_collection()
    return _collection


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up Milvus connection on startup so the first query is fast
    get_col()
    yield


app = FastAPI(title="Synced Brain API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str
    top_k: int = 3
    filters: Optional[dict] = None   # {"source_prefix": "knowledge/ops/", "doc_type": "md"}
    debug: bool = False


class CitationItem(BaseModel):
    source: str
    chunk_index: int
    text: str
    page: Optional[int] = None
    score: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitationItem]
    retrieval: Optional[dict] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_brain(req: QueryRequest):
    # 1) Embed the question
    co = cohere.Client(COHERE_API_KEY)
    try:
        resp = co.embed(
            texts=[req.question],
            model=EMBED_MODEL,
            input_type="search_query",
        )
        query_embedding: list[float] = resp.embeddings[0]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {exc}")

    # 2) Build optional Milvus filter expression
    filter_expr: Optional[str] = None
    if req.filters:
        parts: list[str] = []
        if prefix := req.filters.get("source_prefix"):
            safe = prefix.replace('"', '\\"')
            parts.append(f'source like "{safe}%"')
        if doc_type := req.filters.get("doc_type"):
            safe = doc_type.replace('"', '\\"')
            parts.append(f'doc_type == "{safe}"')
        if parts:
            filter_expr = " and ".join(parts)

    # 3) Vector search
    col = get_col()
    try:
        hits = search(col, query_embedding, top_k=req.top_k, filter_expr=filter_expr)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {exc}")

    if not hits:
        return QueryResponse(
            answer="No relevant information found in the knowledge base.",
            citations=[],
        )

    # 4) Build context for LLM
    context_blocks = [
        f"[{i + 1}] Source: {h['source']}\n{h['chunk_text']}"
        for i, h in enumerate(hits)
    ]
    context = "\n\n---\n\n".join(context_blocks)

    # prompt = (
    #     "You are a helpful assistant with access to a personal knowledge base.\n"
    #     "Answer the question using ONLY the provided context. "
    #     "Be concise and factual. If the answer is not in the context, say so.\n\n"
    #     f"Context:\n{context}\n\n"
    #     f"Question: {req.question}\n\nAnswer:"
    # )

    prompt = (
        "You are a strict retrieval-based assistant.\n"
        "Use ONLY the provided context.\n"
        "Do NOT copy text verbatim.\n"
        "Summarize and synthesize information clearly.\n"
        "If the answer is not present, say: 'Not found in knowledge base.'\n"
        "Use citations like [1], [2] when referring to sources.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {req.question}\n\nAnswer:"
    )
    hits = search(col, query_embedding, top_k=req.top_k, filter_expr=filter_expr)
    # Filter low-quality results
    hits = [h for h in hits if h["score"] > 0.5]

    # # 5) Gemini reasoning
    # try:
    #     client = genai.Client(api_key=GOOGLE_API_KEY)

    #     response = client.models.generate_content(
    #         model="gemini-2.0-flash",
    #         contents=prompt,
    #     )

    #     answer = response.text.strip()
    # except Exception as exc:
    #     answer = f"LLM error ({exc}). Retrieved {len(hits)} chunks — see citations."



    # 5 Grok reasoning
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            # model="llama-3.1-70b-versatile"  if needed more on ROI
            messages=[
                {"role": "system", "content": "Answer using only the provided context."},
                {"role": "user", "content": prompt},
            ],
        )

        answer = response.choices[0].message.content.strip()

    except Exception as exc:
        answer = f"LLM error ({exc}). Retrieved {len(hits)} chunks — see citations."



    # 6) Build citations
    citations = [
        CitationItem(
            source=h["source"],
            chunk_index=h["chunk_index"],
            text=h["chunk_text"],
            page=h["page"] if h.get("page") and h["page"] != -1 else None,
            score=round(h["score"], 4) if req.debug else None,
        )
        for h in hits
    ]

    retrieval_info = (
        {"top_k": req.top_k, "scores": [round(h["score"], 4) for h in hits]}
        if req.debug
        else None
    )

    return QueryResponse(answer=answer, citations=citations, retrieval=retrieval_info)
