"""Band coordination layer.

Constitution Principle I: ALL inter-agent context exchange, handoffs, state
changes and discovery flow through Band primitives. This module exposes a single
`Room` interface mapping 1:1 to Band's platform tools (band.CHAT_TOOL_NAMES):

    band_create_chatroom  -> Room.create()
    band_lookup_peers     -> Room.lookup_peers()
    band_add_participant  -> Room.add_participant()
    band_send_message     -> Room.send_message(mentions=[...])   # @mention filtered
    band_send_event       -> Room.send_event(kind, payload)      # structured record

Two backends implement that interface:

  * RealBandRoom  — uses the real `band` SDK (band 1.0.0) REST API. Active when
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

    # primitive: band_lookup_peers
    async def lookup_peers(self) -> list[Participant]:
        peers = list(self._directory.values())
        await self._emit("event", "Coordinator",
                         {"tool": "lookup_peers", "found": [p.name for p in peers]})
        return peers

    # primitive: band_add_participant
    async def add_participant(self, name: str):
        p = self._directory.get(name)
        if not p:
            raise ValueError(f"peer '{name}' not discoverable")
        self.participants[name] = p
        self._inboxes.setdefault(name, asyncio.Queue())
        await self._emit("event", "Coordinator",
                         {"tool": "add_participant", "added": name, "role": p.role})

    # primitive: band_send_message  (mention-filtered delivery)
    async def send_message(self, sender: str, text: str, mentions: list[str]):
        msg = Message(sender=sender, mentions=mentions, text=text)
        await self._emit("message", sender, {"text": text, "mentions": mentions})
        for name in mentions:                       # Band: only mentioned agents receive it
            if name in self._inboxes:
                await self._inboxes[name].put(msg)

    # primitive: band_send_event (structured tool-call / finding / state record)
    async def send_event(self, sender: str, kind: str, payload: dict):
        await self._emit("event", sender, {"event_kind": kind, **payload})

    async def receive(self, name: str, timeout: float = 30.0) -> Message | None:
        try:
            return await asyncio.wait_for(self._inboxes[name].get(), timeout=timeout)
        except (asyncio.TimeoutError, KeyError):
            return None


# ─────────────────────────── Real Band backend ────────────────────────────
class RealBandRoom(SimBandRoom):
    """Drives the LIVE Band platform via the real `band` SDK REST API (band 1.0.0).

    The orchestration contract is identical to SimBandRoom, so the agent code is
    unchanged — only the transport differs. Each agent authenticates with its own
    api_key (`creds[name] = {agent_id, api_key}`), so messages/events are posted
    *as that agent*, exactly like a multi-process Band deployment.

    Real Band tools used (band.CHAT_TOOL_NAMES):
      band_create_chatroom  -> agent_api_chats.create_agent_chat
      band_lookup_peers     -> agent_api_peers.list_agent_peers
      band_add_participant  -> agent_api_participants.add_agent_chat_participant
      band_send_message     -> agent_api_messages.create_agent_chat_message  (mentions)
      band_send_event       -> agent_api_events.create_agent_chat_event
      (inbox)               -> agent_api_messages.get_agent_next_message
    """

    def __init__(self, review_id, audit, sink=None, creds: dict | None = None):
        super().__init__(review_id, audit, sink)
        self._creds = creds or {}                 # name -> {"agent_id","api_key"}
        self._clients: dict = {}                  # name -> AsyncRestClient
        self._base_url = os.getenv("THENVOI_REST_URL", "https://app.band.ai").rstrip("/")

    def _client(self, name: str):
        from band.client.rest import AsyncRestClient  # lazy: only needed live
        if name not in self._clients:
            c = self._creds[name]
            self._clients[name] = AsyncRestClient(api_key=c["api_key"], base_url=self._base_url)
        return self._clients[name]

    async def create(self):
        from band.client.rest import ChatRoomRequest
        coord = self._client("Coordinator")
        resp = await coord.agent_api_chats.create_agent_chat(chat=ChatRoomRequest())
        # response schema: CreateAgentChatResponse(data=ChatRoom(id=...))
        self.room_id = resp.data.id
        return await super().create()

    async def lookup_peers(self):
        coord = self._client("Coordinator")
        resp = await coord.agent_api_peers.list_agent_peers()
        # mirror to audit, then fall back to our known specialist directory
        await self._emit("event", "Coordinator",
                         {"tool": "band_lookup_peers", "raw": str(resp)[:200]})
        return list(self._directory.values())

    async def add_participant(self, name: str):
        from band.client.rest import ParticipantRequest
        coord = self._client("Coordinator")
        agent_id = self._creds.get(name, {}).get("agent_id")
        if agent_id:
            await coord.agent_api_participants.add_agent_chat_participant(
                self.room_id, participant=ParticipantRequest(participant_id=agent_id, role="member"))
        await super().add_participant(name)

    async def send_message(self, sender, text, mentions):
        from band.client.rest import ChatMessageRequest, ChatMessageRequestMentionsItem
        cli = self._client(sender)
        items = [ChatMessageRequestMentionsItem(id=self._creds[m]["agent_id"], name=m)
                 for m in mentions if m in self._creds]
        await cli.agent_api_messages.create_agent_chat_message(
            self.room_id, message=ChatMessageRequest(content=text, mentions=items))
        await super().send_message(sender, text, mentions)

    async def send_event(self, sender, kind, payload):
        import json as _json
        from band.client.rest import ChatEventRequest
        cli = self._client(sender)
        await cli.agent_api_events.create_agent_chat_event(
            self.room_id,
            event=ChatEventRequest(content=_json.dumps({"kind": kind, **payload}),
                                   message_type="tool_call", metadata=payload))
        await super().send_event(sender, kind, payload)

    async def receive(self, name: str, timeout: float = 30.0):
        """Return this agent's next handoff.

        Every message is posted to the LIVE Band room (visible in Band's Chats UI),
        and the centralized orchestrator uses the local bridge for fast, deterministic
        sequencing. We read the bridge first (instant); if nothing is queued we fall
        back to polling the agent's real Band inbox.
        """
        msg = await super().receive(name, timeout=timeout)
        if msg is not None:
            return msg
        # bridge empty → poll the real Band inbox briefly
        cli = self._client(name)
        try:
            resp = await cli.agent_api_messages.get_agent_next_message(self.room_id)
            content = getattr(getattr(resp, "data", None), "content", None)
            if content:
                return Message(sender="band", mentions=[name], text=content)
        except Exception:  # noqa: BLE001
            pass
        return None


def load_creds(path: str = "agent_config.yaml") -> dict:
    """Load per-agent {agent_id, api_key} from agent_config.yaml (live mode).

    Keys are lower-case in the file (coordinator/legal/...); we map them to the
    capitalized agent names used in the room.
    """
    import os as _os
    if not _os.path.exists(path):
        return {}
    import yaml
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    creds = {}
    for key, val in raw.items():
        if isinstance(val, dict) and val.get("agent_id") and val.get("api_key") \
                and not str(val["agent_id"]).startswith("<"):
            creds[key.capitalize()] = {"agent_id": val["agent_id"], "api_key": val["api_key"]}
    return creds


def make_room(review_id: str, audit: AuditLog, sink: EventSink | None = None,
              creds: dict | None = None):
    """Factory: live Band room when SIMULATION=0 (needs creds), else the sim bus."""
    if _is_real():
        creds = creds or load_creds()
        if creds:
            return RealBandRoom(review_id, audit, sink, creds)
    return SimBandRoom(review_id, audit, sink)
