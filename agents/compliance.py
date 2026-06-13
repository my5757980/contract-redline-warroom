"""Compliance agent — policy/regulatory check via the Featherless open-source path.

Can emit a VETO, which forces the Coordinator into a visible re-plan loop
(Principle: real coordination, not a linear pipeline).
"""
from __future__ import annotations

from .base import SpecialistAgent
from .common.band_client import SimBandRoom
from .common.contract import Contract

SYSTEM = (
    "You are a compliance officer checking a contract against policy (GDPR/DPA, data "
    "residency, security addendum). Return JSON: {\"verdict\":\"PASS|FAIL\","
    "\"required_addenda\":[...],\"veto\":<bool>,\"citation\":<str>}. Veto only on a "
    "hard policy violation (e.g. personal-data processing without a DPA)."
)


def build() -> SpecialistAgent:
    # use_featherless=True → routes through Featherless AI (partner prize evidence)
    return SpecialistAgent(name="Compliance", role="Checks policy & regulatory compliance",
                           system_prompt=SYSTEM, use_featherless=True)


async def run(agent: SpecialistAgent, contract: Contract, room: SimBandRoom,
              prior: dict, replan: bool = False) -> dict:
    await room.receive("Compliance", timeout=60)
    extra = " The Coordinator added the required addenda; re-evaluate." if replan else ""
    out = agent._think(
        f"Financials & risk: {prior}\nContract title: {contract.title}.{extra}\n"
        "Mentions personal data? Return the compliance JSON."
    )
    await room.send_event("Compliance", "compliance_verdict", {
        "verdict": out.get("verdict"), "required_addenda": out.get("required_addenda", []),
        "veto": bool(out.get("veto")), "citation": out.get("citation"),
        "provider": out.get("_provider"), "replan": replan,
    })
    if out.get("veto") and not replan:
        await room.send_message("Compliance",
                                "VETO: personal-data clause lacks a DPA. Coordinator, please "
                                "attach the required addenda and re-circulate.",
                                mentions=["Coordinator"])
    else:
        await room.send_message("Compliance",
                                f"Compliance {out.get('verdict')}. Coordinator, ready for sign-off.",
                                mentions=["Coordinator"])
    return out
