"""Finance agent — extracts payment terms and computes worst-case exposure."""
from __future__ import annotations

from .base import SpecialistAgent
from .common.band_client import SimBandRoom
from .common.contract import Contract

SYSTEM = (
    "You are a finance controller. Extract payment terms, caps and penalties and "
    "compute financial exposure. Return JSON: {\"annual_value_usd\":<int>,"
    "\"worst_case_usd\":<int>,\"penalties\":<str>,\"citation\":<str>}."
)


def build() -> SpecialistAgent:
    return SpecialistAgent(name="Finance", role="Computes financial exposure", system_prompt=SYSTEM)


async def run(agent: SpecialistAgent, contract: Contract, room: SimBandRoom, prior: dict) -> dict:
    await room.receive("Finance", timeout=60)
    out = agent._think(
        f"Risk assessment: {prior}\n\nContract clauses mention fees/penalties. "
        "Return the finance JSON."
    )
    await room.send_event("Finance", "financials", {
        "annual_value_usd": out.get("annual_value_usd"),
        "worst_case_usd": out.get("worst_case_usd"),
        "penalties": out.get("penalties"), "citation": out.get("citation"),
        "provider": out.get("_provider"),
    })
    await room.send_message("Finance",
                            f"Worst-case exposure ~${out.get('worst_case_usd')}. "
                            "Compliance, please run the policy check.",
                            mentions=["Compliance"])
    return out
