"""The three promises of the War Room, each tested where it can break:

* a Compliance veto that survives the re-plan is never waved through to sign-off;
* the audit chain detects a changed actor, kind or review, and anything added after the seal;
* only an authenticated human reviewer can seal a decision, under their own name;
* only an authenticated reviewer can start a review (each one spends LLM credits), and its ID can't be guessed.

Runs offline in SIMULATION mode.  From the repo root:  python -m pytest tests
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents import coordinator
from agents.common import llm
from agents.common.audit import AuditLog
from agents.common.contract import ingest

TOKEN = "t0k3n-for-tests-only-0123456789"


# ── Compliance veto ─────────────────────────────────────────────────────────
async def review(monkeypatch, tmp_path, *, veto_on_replan: bool):
    """A low-risk, low-value contract whose Compliance check vetoes (and maybe keeps vetoing)."""
    real_reason = llm.reason

    def reason(system, user, temperature=0.2):
        s = system.lower()
        if "risk officer" in s:
            return llm.LLMResult(json.dumps({"severity": "low", "exposure_usd": 1000, "citation": "c"}), "test")
        if "finance controller" in s:
            return llm.LLMResult(json.dumps({"annual_value_usd": 12000, "worst_case_usd": 1000, "citation": "c"}), "test")
        return real_reason(system, user, temperature)

    def classify(system, user, temperature=0.0):
        veto = veto_on_replan or "re-evaluate" not in user
        return llm.LLMResult(json.dumps({
            "verdict": "FAIL" if veto else "PASS", "veto": veto,
            "required_addenda": ["GDPR DPA"] if veto else [], "citation": "personal data clause",
        }), "test")

    monkeypatch.setattr(llm, "reason", reason)
    monkeypatch.setattr(llm, "classify", classify)
    events = []
    contract = ingest(Path("samples/sample_msa.txt").read_text(encoding="utf-8"), title="MSA")
    res = await coordinator.run_review(contract, "rev_t", AuditLog(str(tmp_path / "t.db")), sink=events.append)
    said = [e["payload"]["text"] for e in events if e["kind"] == "message" and e["actor"] == "Compliance"]
    kinds = [e["payload"].get("event_kind") for e in events if e["kind"] == "event"]
    return res["packet"], said, kinds


async def test_a_veto_that_survives_the_replan_is_never_recommended_for_approval(monkeypatch, tmp_path):
    packet, said, kinds = await review(monkeypatch, tmp_path, veto_on_replan=True)
    assert packet["recommendation"] == "REJECT"          # the score alone would say APPROVE
    assert packet["compliance"]["veto"] is True
    assert "ready for sign-off" not in said[-1] and "VETO" in said[-1]
    assert "veto_unresolved" in kinds


async def test_a_veto_resolved_by_the_replan_proceeds_normally(monkeypatch, tmp_path):
    packet, said, kinds = await review(monkeypatch, tmp_path, veto_on_replan=False)
    assert packet["recommendation"] == "APPROVE"
    assert packet["compliance"]["veto"] is False
    assert "ready for sign-off" in said[-1]
    assert "veto_unresolved" not in kinds


# ── Audit chain ─────────────────────────────────────────────────────────────
def sealed_chain(tmp_path) -> AuditLog:
    log = AuditLog(str(tmp_path / "audit.db"))
    log.create_review("r1", "c1", "room1")
    log.append("r1", "Compliance", "event", {"veto": True, "citation": "no DPA"})
    log.append("r1", "Risk", "event", {"severity": "high"})
    log.seal("r1", {"action": "reject", "reviewer": "alice"})
    return log


def test_a_clean_chain_verifies(tmp_path):
    assert sealed_chain(tmp_path).verify("r1")["valid"]


@pytest.mark.parametrize("column, value", [("payload_json", '{"veto":false}'), ("actor", "Legal"), ("kind", "message")])
def test_editing_any_field_of_an_entry_is_detected(tmp_path, column, value):
    log = sealed_chain(tmp_path)
    log._conn.execute(f"UPDATE audit_entries SET {column}=? WHERE review_id='r1' AND seq=0", (value,))
    log._conn.commit()
    assert not log.verify("r1")["valid"]


def test_moving_a_chain_to_another_review_is_detected(tmp_path):
    log = sealed_chain(tmp_path)
    log._conn.execute("INSERT INTO audit_entries SELECT 'r2', seq, ts, actor, kind, payload_json, prev_hash, "
                      "entry_hash FROM audit_entries WHERE review_id='r1'")
    log._conn.commit()
    assert not log.verify("r2")["valid"]


def test_an_entry_added_after_the_seal_is_detected(tmp_path):
    log = sealed_chain(tmp_path)
    log.append("r1", "Coordinator", "event", {"note": "slipped in after the decision"})
    assert not log.verify("r1")["valid"]


# ── Human gate ──────────────────────────────────────────────────────────────
@pytest.fixture
def gate(monkeypatch, tmp_path):
    import backend.main as main

    monkeypatch.setattr(main, "audit", AuditLog(str(tmp_path / "gate.db")))
    main.audit.create_review("rev_g", "c1", "room1")
    main.audit.append("rev_g", "Coordinator", "event", {"event_kind": "final_packet"})
    main.audit.append("rev_g", "Coordinator", "event", {"event_kind": "awaiting_human_gate"})
    main.audit.create_review("rev_running", "c2", "room2")      # agents still working
    return main, TestClient(main.app)


def decide(client, token=None, **body):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post("/api/decision", json={"review_id": "rev_g", "action": "approve", **body}, headers=headers)


def test_the_gate_stays_closed_when_no_reviewer_is_configured(gate, monkeypatch):
    main, client = gate
    monkeypatch.delenv("WARROOM_REVIEWERS", raising=False)
    assert decide(client, TOKEN).status_code == 503
    assert main.audit.get_review("rev_g")["root_hash"] is None


@pytest.mark.parametrize("token", [None, "wrong-token"])
def test_a_decision_needs_a_valid_reviewer_token(gate, monkeypatch, token):
    main, client = gate
    monkeypatch.setenv("WARROOM_REVIEWERS", f"alice:{TOKEN}")
    assert decide(client, token).status_code == 401
    assert main.audit.get_review("rev_g")["root_hash"] is None


def test_the_gate_opens_only_once_the_final_packet_is_posted(gate, monkeypatch):
    main, client = gate
    monkeypatch.setenv("WARROOM_REVIEWERS", f"alice:{TOKEN}")
    assert decide(client, TOKEN, review_id="rev_running").status_code == 409
    assert main.audit.get_review("rev_running")["root_hash"] is None


def test_the_seal_names_the_authenticated_reviewer_not_the_claimed_one(gate, monkeypatch):
    main, client = gate
    monkeypatch.setenv("WARROOM_REVIEWERS", f"alice:{TOKEN}, bob:another-long-token-000000")
    r = decide(client, TOKEN, reviewer="mallory", note="looks fine")
    assert r.status_code == 200 and r.json()["sealed"] and r.json()["verify"]["valid"]
    assert main.audit.entries("rev_g")[-1]["payload"]["reviewer"] == "alice"
    assert decide(client, TOKEN).status_code == 409      # sealed once, never again


# ── Starting a review ───────────────────────────────────────────────────────
def start(client, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post("/api/reviews", json={"use_sample": True}, headers=headers)


def stored_contracts(main) -> int:
    return main.audit._conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]


def test_no_review_can_start_when_no_reviewer_is_configured(gate, monkeypatch):
    main, client = gate
    monkeypatch.delenv("WARROOM_REVIEWERS", raising=False)
    assert start(client, TOKEN).status_code == 503
    assert stored_contracts(main) == 0


@pytest.mark.parametrize("token", [None, "wrong-token"])
def test_starting_a_review_needs_a_valid_reviewer_token(gate, monkeypatch, token):
    main, client = gate
    monkeypatch.setenv("WARROOM_REVIEWERS", f"alice:{TOKEN}")
    assert start(client, token).status_code == 401
    assert stored_contracts(main) == 0                   # nothing stored, no agent started


def test_a_reviewer_starts_a_review_whose_id_cannot_be_guessed(gate, monkeypatch):
    main, client = gate
    monkeypatch.setenv("WARROOM_REVIEWERS", f"alice:{TOKEN}")
    r = start(client, TOKEN)
    assert r.status_code == 200 and stored_contracts(main) == 1
    assert len(r.json()["review_id"].removeprefix("rev_")) == 32      # 128 random bits, not 32
