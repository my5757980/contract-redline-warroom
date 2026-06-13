"""Legal agent — redlines risky clauses with citations."""
from __future__ import annotations

from .base import SpecialistAgent
from .common.band_client import SimBandRoom
from .common.contract import Contract

SYSTEM = (
    "You are senior legal counsel reviewing a commercial contract. Identify risky "
    "clauses (liability, indemnity, IP ownership, termination, governing law). "
    "Return JSON: {\"findings\":[{\"section\",\"issue\",\"severity\":\"low|medium|high\","
    "\"suggested\",\"citation\"}]}. Every finding MUST quote source text in `citation`."
)


def build() -> SpecialistAgent:
    return SpecialistAgent(name="Legal", role="Redlines risky legal clauses", system_prompt=SYSTEM)


async def run(agent: SpecialistAgent, contract: Contract, room: SimBandRoom) -> dict:
    # wait for the Coordinator's @mention handoff
    await room.receive("Legal", timeout=60)
    text = "\n\n".join(f"[{c.section}] {c.title}\n{c.cite(220)}" for c in contract.clauses)
    out = agent._think(f"Contract clauses:\n{text}\n\nReturn the redline findings JSON.")
    findings = out.get("findings", [])
    for f in findings:
        await room.send_event("Legal", "redline", {
            "section": f.get("section"), "issue": f.get("issue"),
            "severity": f.get("severity"), "suggested": f.get("suggested"),
            "citation": f.get("citation"), "provider": out.get("_provider"),
        })
    await room.send_message("Legal",
                            f"Posted {len(findings)} redline(s). Risk, please quantify exposure.",
                            mentions=["Risk"])
    return {"redlines": findings, "provider": out.get("_provider")}
