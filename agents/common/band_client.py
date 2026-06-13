"""Band coordination layer.

Constitution Principle I: ALL inter-agent context exchange, handoffs, state
changes and discovery flow through Band primitives. This module exposes a single
`Room` interface mapping 1:1 to Band's platform tools:

    create_chatroom   -> Room.create()
    thenvoi_lookup_peers     -> Room.lookup_peers()
    thenvoi_add_participant  -> Room.add_participant()
    thenvoi_send_message     -> Room.send_message(mentions=[...])   # @mention filtered
    thenvoi_send_event       -> Room.send_event(kind, payload)      # structured record

Two backends implement that interface:

  * RealBandRoom  — uses the `band-sdk` (`thenvoi`) WebSocket platform. Active when
                    SIMULATION=0 and agent_config.yaml + THENVOI_* env are present.
  * SimBandRoom   — a faithful in-process Band-semantics bus (mention-based delivery,
                    structured events, peer registry). Default for offline, demo-safe
                    runs. It is NOT a stub of the logic — it reproduces Band's
                    message-routing contract so the same agent code runs unchanged.

Every primitive mirrors into the hash-chained AuditLog and an async event sink the
backend streams to the War Room UI.
"""
from __future__ import annotations

import asyncio
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from .audit import AuditLog

EventSink = Callable[[dict], Awaitable[None] | None]


@dataclass
class Participant:
    name: str            # e.g. "Legal", "Risk" (used as the @mention handle)
    role: str            # human-readable charter
    agent_id: str = ""   # Band agent UUID (real mode)


@dataclass
class Message:
    sender: str
    mentions: list[str]
    text: str
    ts: float = field(default_factory=time.time)


def _is_real() -> bool:
    return os.getenv("SIMULATION", "1") == "0"


# ─────────────────────────── Simulation backend ───────────────────────────
class SimBandRoom:
    """In-process implementation of Band's room contract."""

    def __init__(self, review_id: str, audit: AuditLog, sink: EventSink | None = None):
        self.review_id = review_id
        self.audit = audit
        self.sink = sink
        self.room_id = "room_" + uuid.uuid4().hex[:10]
        self.participants: dict[str, Participant] = {}
        # Band delivers a message only to mentioned participants -> one inbox queue each
        self._inboxes: dict[str, asyncio.Queue[Message]] = {}
        # global registry of discoverable peers (Band's lookup_peers)
        self._directory: dict[str, Participant] = {}

    async def _emit(self, kind: str, actor: str, payload: dict):
        entry = self.audit.append(self.review_id, actor=actor, kind=kind, payload=payload)
        event = {"review_id": self.review_id, "room_id": self.room_id, "kind": kind,
                 "actor": actor, "payload": payload, "seq": entry.seq,
                 "hash": entry.entry_hash, "ts": entry.ts}
        if self.sink:
            res = self.sink(event)
            if asyncio.iscoroutine(res):
                await res
        return event

    # primitive: create_chatroom
    async def create(self):
        await self._emit("state", "Coordinator",
                         {"action": "create_chatroom", "room_id": self.room_id})
        return self.room_id

    # primitive: register a discoverable agent (Band agents announce themselves)
    def register_peer(self, p: Participant):
        self._directory[p.name] = p
        self._inboxes.setdefault(p.name, asyncio.Queue())

    # primitive: thenvoi_lookup_peers
    async def lookup_peers(self) -> list[Participant]:
        peers = list(self._directory.values())
        await self._emit("event", "Coordinator",
                         {"tool": "lookup_peers", "found": [p.name for p in peers]})
        return peers

    # primitive: thenvoi_add_participant
    async def add_participant(self, name: str):
        p = self._directory.get(name)
        if not p:
            raise ValueError(f"peer '{name}' not discoverable")
        self.participants[name] = p
        self._inboxes.setdefault(name, asyncio.Queue())
        await self._emit("event", "Coordinator",
                         {"tool": "add_participant", "added": name, "role": p.role})

    # primitive: thenvoi_send_message  (mention-filtered delivery)
    async def send_message(self, sender: str, text: str, mentions: list[str]):
        msg = Message(sender=sender, mentions=mentions, text=text)
        await self._emit("message", sender, {"text": text, "mentions": mentions})
        for name in mentions:                       # Band: only mentioned agents receive it
            if name in self._inboxes:
                await self._inboxes[name].put(msg)

    # primitive: thenvoi_send_event (structured tool-call / finding / state record)
    async def send_event(self, sender: str, kind: str, payload: dict):
        await self._emit("event", sender, {"event_kind": kind, **payload})

    async def receive(self, name: str, timeout: float = 30.0) -> Message | None:
        try:
            return await asyncio.wait_for(self._inboxes[name].get(), timeout=timeout)
        except (asyncio.TimeoutError, KeyError):
            return None


# ─────────────────────────── Real Band backend ────────────────────────────
class RealBandRoom(SimBandRoom):
    """Thin wrapper that drives the actual band-sdk platform.

    The orchestration contract is identical to SimBandRoom, so agent code is
    unchanged. Only the transport differs: here primitives call the live thenvoi
    platform tools over the WebSocket established by `Agent.create(...).run()`.
    Falls back to simulation semantics for local fan-out bookkeeping while the
    real platform handles cross-process delivery.
    """

    def __init__(self, review_id, audit, sink=None, agents: dict | None = None):
        super().__init__(review_id, audit, sink)
        self._agents = agents or {}   # name -> live thenvoi Agent handle

    async def create(self):
        # In real mode the Coordinator agent calls thenvoi_create_chatroom.
        coord = self._agents.get("Coordinator")
        if coord is not None:
            self.room_id = await coord.tools.thenvoi_create_chatroom(  # type: ignore[attr-defined]
                name=f"contract-{self.review_id}")
        return await super().create()

    async def add_participant(self, name: str):
        coord = self._agents.get("Coordinator")
        peer = self._directory.get(name)
        if coord is not None and peer is not None:
            await coord.tools.thenvoi_add_participant(  # type: ignore[attr-defined]
                chat_id=self.room_id, agent_id=peer.agent_id)
        await super().add_participant(name)

    async def send_message(self, sender, text, mentions):
        agent = self._agents.get(sender)
        if agent is not None:
            mention_str = " ".join(f"@{m}" for m in mentions)
            await agent.tools.thenvoi_send_message(  # type: ignore[attr-defined]
                chat_id=self.room_id, content=f"{mention_str} {text}")
        await super().send_message(sender, text, mentions)

    async def send_event(self, sender, kind, payload):
        agent = self._agents.get(sender)
        if agent is not None:
            await agent.tools.thenvoi_send_event(  # type: ignore[attr-defined]
                chat_id=self.room_id, event_type=kind, data=payload)
        await super().send_event(sender, kind, payload)


def make_room(review_id: str, audit: AuditLog, sink: EventSink | None = None,
              agents: dict | None = None):
    """Factory: real Band room when SIMULATION=0, else the simulation bus."""
    if _is_real():
        return RealBandRoom(review_id, audit, sink, agents)
    return SimBandRoom(review_id, audit, sink)
