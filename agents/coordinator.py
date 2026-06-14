"""Coordinator agent + the full review engine.

Opens the Band room, discovers and recruits the 4 specialists through Band
primitives, sequences the workflow with @mention handoffs, enforces the citation
rule, handles a Compliance VETO with a visible re-plan loop, aggregates a single
exposure score, posts the final packet, and requests the human gate.

`run_review(...)` is the entry point the backend calls.
"""
from __future__ import annotations

from . import legal, risk, finance, compliance
from .common.audit import AuditLog
from .common.band_client import make_room, SimBandRoom
from .common.contract import Contract

SPECIALISTS = ("Legal", "Risk", "Finance", "Compliance")


def _to_usd(val) -> float | None:
    """Coerce a finance-agent USD value to a number, or None if non-numeric
    (e.g. the LLM answers "unlimited" for an uncapped liability clause)."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.replace(",", "").replace("$", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _exposure_score(risk_out: dict, fin_out: dict, comp_out: dict) -> int:
    """Blend severity, dollar worst-case and compliance into a 0–100 score."""
    sev = {"low": 20, "medium": 55, "high": 85}.get((risk_out.get("severity") or "").lower(), 40)
    worst = _to_usd(fin_out.get("worst_case_usd"))
    # non-numeric worst-case (e.g. "unlimited") -> treat as maximum dollar exposure
    dollar = 100 if worst is None else min(100, worst / 10000)          # $1M worst-case ≈ 100
    comp_pen = 100 if comp_out.get("verdict") == "FAIL" else 0
    score = round(0.4 * sev + 0.35 * dollar + 0.25 * comp_pen)
    return max(0, min(100, score))


async def run_review(contract: Contract, review_id: str, audit: AuditLog,
                     sink=None) -> dict:
    room: SimBandRoom = make_room(review_id, audit, sink)

    # 1) Coordinator opens the room
    await room.create()
    audit.create_review(review_id, contract.id, room.room_id)

    # 2) Build + register the specialists so they are DISCOVERABLE (Band lookup_peers)
    agents = {
        "Legal": legal.build(), "Risk": risk.build(),
        "Finance": finance.build(), "Compliance": compliance.build(),
    }
    for a in agents.values():
        room.register_peer(a.as_participant())

    # 3) Discover peers, then recruit each through Band
    peers = await room.lookup_peers()
    for name in SPECIALISTS:
        await room.add_participant(name)

    await room.send_event("Coordinator", "plan", {
        "contract": contract.title, "clauses": len(contract.clauses),
        "sequence": list(SPECIALISTS),
        "discovered_peers": [p.name for p in peers],
    })

    # 4) Kick off the chain: handoffs happen agent→agent via @mentions
    import asyncio

    async def drive():
        # Coordinator mentions Legal to start
        await room.send_message("Coordinator", "New contract for review. Legal, please redline.",
                                mentions=["Legal"])
        legal_out = await legal.run(agents["Legal"], contract, room)
        # citation rule enforcement
        for f in legal_out.get("redlines", []):
            if not f.get("citation"):
                await room.send_event("Coordinator", "citation_reject",
                                      {"section": f.get("section"), "reason": "missing citation"})
        risk_out = await risk.run(agents["Risk"], contract, room, legal_out)
        fin_out = await finance.run(agents["Finance"], contract, room, risk_out)
        comp_out = await compliance.run(agents["Compliance"], contract, room, fin_out)

        # 5) Compliance VETO → visible re-plan loop
        if comp_out.get("veto"):
            await room.send_event("Coordinator", "replan", {
                "reason": "compliance_veto",
                "remediation": comp_out.get("required_addenda", []),
            })
            await room.send_message("Coordinator",
                                    "Attaching required addenda. Compliance, please re-evaluate.",
                                    mentions=["Compliance"])
            comp_out = await compliance.run(agents["Compliance"], contract, room, fin_out,
                                            replan=True)
        return legal_out, risk_out, fin_out, comp_out

    # specialists wait on their inboxes; drive() feeds them — run concurrently
    legal_out, risk_out, fin_out, comp_out = await drive()

    # 6) Aggregate + post final packet, then request the human gate
    score = _exposure_score(risk_out, fin_out, comp_out)
    audit.set_exposure(review_id, score)
    packet = {
        "exposure_score": score,
        "risk": {"severity": risk_out.get("severity"),
                 "exposure_usd": risk_out.get("exposure_usd")},
        "finance": {"worst_case_usd": fin_out.get("worst_case_usd"),
                    "annual_value_usd": fin_out.get("annual_value_usd")},
        "compliance": {"verdict": comp_out.get("verdict"),
                       "required_addenda": comp_out.get("required_addenda", [])},
        "redlines": legal_out.get("redlines", []),
        "recommendation": "REJECT" if score >= 70 else
                          ("REVIEW" if score >= 40 else "APPROVE"),
    }
    await room.send_event("Coordinator", "final_packet", packet)
    await room.send_event("Coordinator", "awaiting_human_gate",
                          {"message": "Human reviewer must Approve / Reject / Request-Changes."})
    return {"room_id": room.room_id, "packet": packet}
