"""CLI demo runner — ingest a sample contract and run the full Band review.

    uv run python -m agents.run_all                # uses samples/sample_msa.txt
    uv run python -m agents.run_all path/to.txt

Prints the live Band room transcript and the final packet. Works fully offline in
SIMULATION mode; set SIMULATION=0 (with agent_config.yaml + THENVOI_*) for live Band.
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

from .common.audit import AuditLog
from .common.contract import ingest
from .common import llm
from . import coordinator

load_dotenv()

ICON = {"state": "🏛️", "event": "📡", "message": "💬", "seal": "🔏"}


async def _print_sink(ev: dict):
    actor = ev["actor"]
    kind = ev["kind"]
    p = ev["payload"]
    if kind == "message":
        line = f"{', '.join('@'+m for m in p.get('mentions', []))}: {p.get('text','')}"
    elif kind == "event":
        ek = p.get("event_kind") or p.get("tool") or p.get("action") or "event"
        detail = {k: v for k, v in p.items()
                  if k not in ("event_kind", "provider")}
        prov = f" [{p.get('provider')}]" if p.get("provider") else ""
        line = f"{ek}{prov} :: {detail}"
    else:
        line = str(p)
    print(f"  {ICON.get(kind,'•')} #{ev['seq']:>2} {actor:<11} {line}")


async def main():
    path = sys.argv[1] if len(sys.argv) > 1 else str(Path("samples/sample_msa.txt"))
    raw = Path(path).read_text(encoding="utf-8")
    contract = ingest(raw, title=Path(path).stem)
    review_id = "rev_" + uuid.uuid4().hex[:8]
    audit = AuditLog()
    audit.save_contract(contract.id, contract.title, contract.raw_text)
    for c in contract.clauses:
        audit.save_clause(c.id, contract.id, c.section, c.text)

    print(f"\n=== CONTRACT REDLINE WAR ROOM ===  review={review_id}")
    print(f"Contract: {contract.title}  ({len(contract.clauses)} clauses)\n")
    print("--- Band room transcript ---")
    result = await coordinator.run_review(contract, review_id, audit, sink=_print_sink)

    pkt = result["packet"]
    print("\n--- FINAL PACKET ---")
    print(f"  Exposure score : {pkt['exposure_score']}/100")
    print(f"  Recommendation : {pkt['recommendation']}")
    print(f"  Risk           : {pkt['risk']}")
    print(f"  Finance        : {pkt['finance']}")
    print(f"  Compliance     : {pkt['compliance']}")
    print(f"  Redlines       : {len(pkt['redlines'])}")

    # simulate the human gate so the demo seals an auditable decision
    decision = {"action": "request_changes", "reviewer": "demo-operator",
                "note": "Attach DPA + cap liability before approval.",
                "packet_recommendation": pkt["recommendation"]}
    root = audit.seal(review_id, decision)
    print("\n--- HUMAN GATE ---")
    print(f"  Decision   : {decision['action']} by {decision['reviewer']}")
    print(f"  Sealed root: {root}")
    print(f"  Verify     : {audit.verify(review_id)}")
    print(f"\n--- PARTNER MODEL USAGE (prize evidence) ---\n  {llm.usage_report()}")


if __name__ == "__main__":
    asyncio.run(main())
