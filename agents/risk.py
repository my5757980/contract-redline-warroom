"""Risk agent — scores enterprise risk + dollar exposure from Legal's redlines."""
from __future__ import annotations

from .base import SpecialistAgent
from .common.band_client import SimBandRoom
from .common.contract import Contract

SYSTEM = (
    "You are an enterprise risk officer. Given a contract and legal redlines, assess "
    "overall risk. Return JSON: {\"severity\":\"low|medium|high\",\"exposure_usd\":<int>,"
    "\"rationale\":<str>,\"citation\":<str>}. Cite the clause driving the largest risk."
)


def build() -> SpecialistAgent:
    return SpecialistAgent(name="Risk", role="Scores risk and dollar exposure", system_prompt=SYSTEM)


async def run(agent: SpecialistAgent, contract: Contract, room: SimBandRoom, prior: dict) -> dict:
    await room.receive("Risk", timeout=60)
    redlines = prior.get("redlines", [])
    out = agent._think(
        f"Legal redlines: {redlines}\n\nContract title: {contract.title}\n"
        "Return the risk JSON."
    )
    await room.send_event("Risk", "risk_score", {
        "severity": out.get("severity"), "exposure_usd": out.get("exposure_usd"),
        "rationale": out.get("rationale"), "citation": out.get("citation"),
        "provider": out.get("_provider"),
    })
    await room.send_message("Risk",
                            f"Risk = {out.get('severity')} (~${out.get('exposure_usd')}). "
                            "Finance, please compute financial exposure.",
                            mentions=["Finance"])
    return out
