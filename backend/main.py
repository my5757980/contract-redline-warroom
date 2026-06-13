"""Audit/Bridge service — FastAPI.

Responsibilities:
  * accept a contract, run the Band multi-agent review, and STREAM every Band
    primitive to the War Room UI over WebSocket as it happens;
  * mirror everything into the hash-chained audit log (done inside the agents);
  * expose the human gate (Approve/Reject/Request-Changes) which SEALS the root hash;
  * expose audit retrieval + independent verification.

Run:  uv run uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents.common.audit import AuditLog
from agents.common.contract import ingest
from agents.common import llm
from agents import coordinator

load_dotenv()

app = FastAPI(title="Contract Redline War Room", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

audit = AuditLog()

# review_id -> list of subscriber queues (live WS clients)
_subscribers: dict[str, list[asyncio.Queue]] = {}
# review_id -> buffered events (so a client that connects mid-review gets backfill)
_buffer: dict[str, list[dict]] = {}
_results: dict[str, dict] = {}


async def _broadcast(ev: dict):
    rid = ev["review_id"]
    _buffer.setdefault(rid, []).append(ev)
    for q in _subscribers.get(rid, []):
        await q.put(ev)


class StartReview(BaseModel):
    text: str | None = None
    title: str = "Uploaded Contract"
    use_sample: bool = False


class Decision(BaseModel):
    review_id: str
    action: str          # approve | reject | request_changes
    reviewer: str = "operator"
    note: str = ""


@app.get("/")
def war_room():
    return FileResponse(str(Path(__file__).resolve().parent.parent / "web" / "index.html"))


@app.get("/api/health")
def health():
    return {"ok": True, "service": "contract-warroom", "partners": llm.usage_report()}


@app.post("/api/reviews")
async def start_review(body: StartReview):
    if body.use_sample or not body.text:
        text = Path("samples/sample_msa.txt").read_text(encoding="utf-8")
        title = "Sample Vendor MSA"
    else:
        text, title = body.text, body.title
    contract = ingest(text, title=title)
    review_id = "rev_" + uuid.uuid4().hex[:8]
    audit.save_contract(contract.id, contract.title, contract.raw_text)
    for c in contract.clauses:
        audit.save_clause(c.id, contract.id, c.section, c.text)
    _buffer[review_id] = []

    async def _run():
        res = await coordinator.run_review(contract, review_id, audit, sink=_broadcast)
        _results[review_id] = res
        await _broadcast({"review_id": review_id, "kind": "done", "actor": "system",
                          "payload": res["packet"], "seq": -1, "hash": "", "ts": 0})

    asyncio.create_task(_run())
    return {"review_id": review_id, "title": contract.title,
            "clauses": [{"section": c.section, "title": c.title, "cite": c.cite()}
                        for c in contract.clauses]}


@app.get("/api/reviews/{review_id}")
def get_review(review_id: str):
    rev = audit.get_review(review_id)
    if not rev:
        raise HTTPException(404, "unknown review")
    return {"review": rev, "result": _results.get(review_id),
            "events": _buffer.get(review_id, [])}


@app.get("/api/audit/{review_id}")
def get_audit(review_id: str):
    return {"entries": audit.entries(review_id)}


@app.get("/api/verify/{review_id}")
def verify(review_id: str):
    return audit.verify(review_id)


@app.post("/api/decision")
async def decide(d: Decision):
    if d.action not in ("approve", "reject", "request_changes"):
        raise HTTPException(400, "invalid action")
    rev = audit.get_review(d.review_id)
    if not rev:
        raise HTTPException(404, "unknown review")
    if rev.get("root_hash"):
        raise HTTPException(409, "review already sealed")
    root = audit.seal(d.review_id, {"action": d.action, "reviewer": d.reviewer, "note": d.note})
    ev = {"review_id": d.review_id, "kind": "seal", "actor": "human",
          "payload": {"action": d.action, "reviewer": d.reviewer, "note": d.note,
                      "root_hash": root}, "seq": -2, "hash": root, "ts": 0}
    await _broadcast(ev)
    return {"sealed": True, "root_hash": root, "verify": audit.verify(d.review_id)}


@app.websocket("/ws/reviews/{review_id}")
async def ws_reviews(ws: WebSocket, review_id: str):
    await ws.accept()
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(review_id, []).append(q)
    try:
        # backfill anything already emitted before this client connected
        for ev in _buffer.get(review_id, []):
            await ws.send_json(ev)
        while True:
            ev = await q.get()
            await ws.send_json(ev)
    except WebSocketDisconnect:
        pass
    finally:
        _subscribers.get(review_id, []).remove(q)
