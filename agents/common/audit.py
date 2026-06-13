"""Tamper-evident, hash-chained audit log over SQLite.

Constitution Principle IV: every agent message, event, tool call and human
decision is appended to a hash chain. Each entry's hash covers the previous
entry's hash, so any later edit invalidates the whole tail. The final human
decision seals a `root_hash` that can be independently re-verified.

This module has NO Band or network dependency, so it is unit-testable on its own.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def _canonical(payload: Any) -> str:
    """Deterministic JSON so the same logical payload always hashes the same."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash_entry(prev_hash: str, payload: Any, ts: float, seq: int) -> str:
    blob = f"{prev_hash}|{_canonical(payload)}|{ts:.6f}|{seq}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass
class AuditEntry:
    review_id: str
    seq: int
    ts: float
    actor: str          # which agent / "human" / "system"
    kind: str           # message | event | tool_call | decision | seal | state
    payload: dict
    prev_hash: str
    entry_hash: str

    def as_dict(self) -> dict:
        d = asdict(self)
        return d


SCHEMA = """
CREATE TABLE IF NOT EXISTS contracts(
    id TEXT PRIMARY KEY, title TEXT, raw_text TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS clauses(
    id TEXT PRIMARY KEY, contract_id TEXT, section TEXT, text TEXT);
CREATE TABLE IF NOT EXISTS reviews(
    id TEXT PRIMARY KEY, contract_id TEXT, band_room_id TEXT,
    status TEXT, exposure_score INTEGER, root_hash TEXT, sealed_at REAL);
CREATE TABLE IF NOT EXISTS audit_entries(
    review_id TEXT, seq INTEGER, ts REAL, actor TEXT, kind TEXT,
    payload_json TEXT, prev_hash TEXT, entry_hash TEXT,
    PRIMARY KEY(review_id, seq));
"""


class AuditLog:
    def __init__(self, db_path: str = "warroom.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    # ── chain operations ────────────────────────────────────────────────
    def _last(self, review_id: str) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT * FROM audit_entries WHERE review_id=? ORDER BY seq DESC LIMIT 1",
            (review_id,),
        )
        return cur.fetchone()

    def append(self, review_id: str, actor: str, kind: str, payload: dict) -> AuditEntry:
        last = self._last(review_id)
        prev_hash = last["entry_hash"] if last else GENESIS
        seq = (last["seq"] + 1) if last else 0
        ts = time.time()
        entry_hash = _hash_entry(prev_hash, payload, ts, seq)
        self._conn.execute(
            "INSERT INTO audit_entries VALUES (?,?,?,?,?,?,?,?)",
            (review_id, seq, ts, actor, kind, _canonical(payload), prev_hash, entry_hash),
        )
        self._conn.commit()
        return AuditEntry(review_id, seq, ts, actor, kind, payload, prev_hash, entry_hash)

    def seal(self, review_id: str, decision: dict) -> str:
        """Append the terminal human-decision SEAL entry; returns the root hash."""
        entry = self.append(review_id, actor="human", kind="seal", payload=decision)
        self._conn.execute(
            "UPDATE reviews SET status=?, root_hash=?, sealed_at=? WHERE id=?",
            (decision.get("action", "sealed"), entry.entry_hash, entry.ts, review_id),
        )
        self._conn.commit()
        return entry.entry_hash

    def verify(self, review_id: str) -> dict:
        """Recompute the whole chain; report validity and the root hash."""
        rows = self._conn.execute(
            "SELECT * FROM audit_entries WHERE review_id=? ORDER BY seq ASC",
            (review_id,),
        ).fetchall()
        prev = GENESIS
        for r in rows:
            payload = json.loads(r["payload_json"])
            recomputed = _hash_entry(prev, payload, r["ts"], r["seq"])
            if recomputed != r["entry_hash"] or r["prev_hash"] != prev:
                return {"valid": False, "broken_at_seq": r["seq"], "root_hash": None}
            prev = r["entry_hash"]
        return {"valid": True, "entries": len(rows), "root_hash": prev if rows else None}

    def entries(self, review_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM audit_entries WHERE review_id=? ORDER BY seq ASC",
            (review_id,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d.pop("payload_json"))
            out.append(d)
        return out

    # ── convenience for reviews/contracts ──────────────────────────────
    def save_contract(self, cid: str, title: str, raw_text: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO contracts VALUES (?,?,?,?)",
            (cid, title, raw_text, time.time()),
        )
        self._conn.commit()

    def save_clause(self, clause_id: str, contract_id: str, section: str, text: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO clauses VALUES (?,?,?,?)",
            (clause_id, contract_id, section, text),
        )
        self._conn.commit()

    def create_review(self, review_id: str, contract_id: str, band_room_id: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO reviews VALUES (?,?,?,?,?,?,?)",
            (review_id, contract_id, band_room_id, "in_review", 0, None, None),
        )
        self._conn.commit()

    def set_exposure(self, review_id: str, score: int):
        self._conn.execute(
            "UPDATE reviews SET exposure_score=? WHERE id=?", (score, review_id)
        )
        self._conn.commit()

    def get_review(self, review_id: str) -> dict | None:
        r = self._conn.execute(
            "SELECT * FROM reviews WHERE id=?", (review_id,)
        ).fetchone()
        return dict(r) if r else None


if __name__ == "__main__":
    # tiny self-test: build a chain, tamper, prove verify catches it
    import os, tempfile

    p = os.path.join(tempfile.gettempdir(), "audit_selftest.db")
    if os.path.exists(p):
        os.remove(p)
    log = AuditLog(p)
    log.create_review("r1", "c1", "room1")
    log.append("r1", "legal", "event", {"redline": "liability uncapped", "section": "8.2"})
    log.append("r1", "risk", "event", {"severity": "high", "exposure_usd": 500000})
    root = log.seal("r1", {"action": "approve", "reviewer": "demo"})
    print("sealed root:", root[:16], "...")
    print("verify clean:", log.verify("r1"))
    # tamper
    log._conn.execute("UPDATE audit_entries SET payload_json=? WHERE review_id='r1' AND seq=1",
                      (json.dumps({"severity": "low", "exposure_usd": 1}),))
    log._conn.commit()
    print("verify tampered:", log.verify("r1"))
