"""Specialist agent base: a single-responsibility Band participant.

Each specialist waits for an @mention in the Band room, reads the cited clauses,
reasons with its partner-model path, then posts STRUCTURED findings back to the
room as events and hands off to the next agent with an @mention. No specialist
ever talks to another except through the Band room (Principle I).
"""
from __future__ import annotations

from dataclasses import dataclass

from .common.band_client import Participant, SimBandRoom
from .common.contract import Contract
from .common import llm


@dataclass
class SpecialistAgent:
    name: str
    role: str
    system_prompt: str
    use_featherless: bool = False   # Compliance uses the open-source path

    def as_participant(self) -> Participant:
        return Participant(name=self.name, role=self.role)

    def _think(self, user: str) -> dict:
        fn = llm.classify if self.use_featherless else llm.reason
        res = fn(self.system_prompt, user)
        out = llm.extract_json(res.text)
        out["_provider"] = res.provider
        out["_degraded"] = res.degraded
        return out

    async def review(self, contract: Contract, room: SimBandRoom, prior: dict) -> dict:
        """Override in subclass-style functions; default echoes a no-op."""
        raise NotImplementedError
