# Implementation Plan — Contract Redline War Room

**Feature:** 001-contract-redline-warroom
**Date:** 2026-06-13

---

## 1. Architecture Overview

```
                         ┌──────────────────────────────────────────┐
                         │            BAND PLATFORM (hosted)         │
                         │   Room: "contract-<id>"  (transcript =    │
                         │   single source of truth)                │
                         └──────────────────────────────────────────┘
        thenvoi WebSocket  ▲  ▲  ▲  ▲  ▲   (send_message / send_event /
                           │  │  │  │  │    lookup_peers / add_participant)
   ┌───────────┬───────────┼──┼──┼──┼──┼───────────┬───────────────┐
   │           │           │  │  │  │  │           │               │
┌──┴───┐   ┌───┴────┐  ┌───┴──┴──┴──┴──┴──┐   ┌────┴────┐     ┌─────┴─────┐
│Coord │   │ Legal  │  │ Risk   Finance   │   │Compliance│     │ Audit/    │
│agent │   │ agent  │  │ agent   agent    │   │  agent   │     │ Bridge    │
└──┬───┘   └────────┘  └──────────────────┘   └─────────┘     │ (FastAPI) │
   │  each agent: band-sdk Agent + adapter(claude_sdk)        └─────┬─────┘
   │                                                                │
   │  reasoning calls ──► AI/ML API (primary)                       │ mirrors every
   │  compliance path ──► Featherless AI (open-source inference)    │ Band event into
   │                                                                │ hash-chained SQLite
   └────────────────────────────────────────────────────────────► WebSocket ──► Next.js War Room UI
```

### Components
1. **Agent layer** (`agents/`) — 5 Python processes (or one supervisor spawning 5 `Agent.create`),
   each a Band remote agent using the `claude_sdk`/`anthropic` adapter. Custom LangChain `@tool`s give
   each agent its specialty actions (e.g., `cite_clause`, `score_risk`, `compute_exposure`,
   `check_policy`).
2. **Reasoning gateway** (`agents/llm.py`) — thin client that routes each agent's model calls to
   **AI/ML API** (OpenAI-compatible base URL), with the **Compliance classifier** path routed to
   **Featherless AI**. Deterministic fallback if a partner is unavailable.
3. **Audit/Bridge service** (`backend/`) — FastAPI app that (a) joins the Band room as an observer agent
   to mirror every message/event into the **hash-chained audit log** (SQLite), (b) exposes REST
   (`/contracts`, `/reviews/{id}`, `/audit/{id}`, `/verify/{id}`, human gate `/decision`), and (c) pushes
   live updates to the UI over WebSocket.
4. **War Room UI** (`web/`) — Next.js 15 + Tailwind. Four panels: Room transcript (agent lanes),
   Exposure dashboard, Redline list (with citations), Audit chain viewer + Approve/Reject/Request-Changes.
5. **Replay mode** — the audit log fully reconstructs a past review; UI can play it back without a live
   Band connection (judging safety net).

## 2. Key Decisions & Rationale (ADR candidates)

| # | Decision | Options considered | Choice & why |
|---|---|---|---|
| D1 | Inter-agent coordination | Direct Python calls / message queue / **Band** | **Band** — hackathon mandate + it is genuinely the collaboration substrate; everything routes through Band primitives. |
| D2 | Agent framework | Raw API loop / CrewAI / LangGraph via band-sdk adapter | **band-sdk `claude_sdk`/`langgraph` adapter** — first-class Band integration + Claude reasoning (mirrors showcased winners). |
| D3 | Model routing for partner prizes | Single provider / **dual: AI/ML API + Featherless** | **Dual** — AI/ML API as primary reasoning gateway, Featherless for a specialist open-source inference path → eligible for BOTH partner prizes. |
| D4 | Audit integrity | Plain log / DB rows / **hash-chained log + sealed root** | **Hash chain** — tamper-evident, independently verifiable; the "no black box" differentiator. |
| D5 | Human gate | Auto-approve threshold / **explicit human decision** | **Explicit human** — required by regulated workflow; agents never set final status. |

## 3. API Contracts (Audit/Bridge service)

- `POST /api/contracts` → `{contract_id}` (upload text/PDF; chunk into clauses).
- `POST /api/reviews` `{contract_id}` → `{review_id}` (Coordinator opens Band room, recruits agents).
- `GET  /api/reviews/{id}` → live state: agents present, findings, exposure, status.
- `GET  /api/audit/{id}` → ordered hash-chained entries.
- `POST /api/decision` `{review_id, action: approve|reject|request_changes, reviewer, note}` → seals root hash.
- `GET  /api/verify/{id}` → `{valid: bool, root_hash}` (recompute chain).
- `WS   /ws/reviews/{id}` → stream of `{type, agent, payload, hash}` events.

Errors: `400` bad input, `404` unknown id, `409` decision on already-sealed review, `502` partner API
failure (falls back to deterministic model, surfaced in audit as `degraded:true`).

## 4. Data Model (SQLite)

- `contracts(id, title, raw_text, created_at)`
- `clauses(id, contract_id, section, text)`
- `reviews(id, contract_id, band_room_id, status, exposure_score, root_hash, sealed_at)`
- `audit_entries(id, review_id, seq, ts, actor, kind, payload_json, prev_hash, entry_hash)`
  - `entry_hash = sha256(prev_hash + canonical(payload) + ts + seq)`

## 5. Audit Hash Chain (algorithm)

1. Genesis entry per review: `prev_hash = "0"*64`.
2. Each Band event/message/tool-call/human-decision → append entry with `entry_hash` over
   `prev_hash + canonical_json(payload) + ts + seq`.
3. On human decision, append a terminal `SEAL` entry; `reviews.root_hash = last entry_hash`.
4. `verify` recomputes every `entry_hash` in order; any mismatch ⇒ tampered.

## 6. Non-Functional Budgets

- End-to-end demo review < 3 min. Each agent turn target < 20s.
- UI first paint < 2s; live event latency < 500ms over local WS.
- Zero secrets in repo; `.env` + `agent_config.yaml` git-ignored; MIT license.

## 7. Repo Layout

```
contract-warroom/
├── agents/            # 5 Band agents + tools + llm gateway + supervisor
│   ├── common/        # band client, audit emitter, llm router (AI/ML API + Featherless)
│   ├── coordinator.py legal.py risk.py finance.py compliance.py
│   └── run_all.py     # spawn all agents
├── backend/           # FastAPI audit/bridge + WebSocket + SQLite
├── web/               # Next.js 15 War Room UI
├── samples/           # sample contracts + recorded replay
├── specs/ .specify/ history/   # SDD artifacts, ADRs, PHRs
├── .env.example  agent_config.example.yaml  README.md  LICENSE
```

## 8. Risk Mitigations / Kill Switches

- **Replay mode** flag (`REPLAY=1`) → UI + bridge reconstruct from audit log; no live Band needed.
- **Partner fallback** → if AI/ML API or Featherless errors, deterministic local stub keeps the demo
  alive; audit marks `degraded:true`.
- **Rate caps** → cache identical model calls per review.

## 9. Definition of Done

Matches constitution DoD: ≥4 agents collaborating through Band with handoffs + a visible veto/re-plan,
clause-cited findings, human gate, verifiable sealed audit hash, both partner APIs exercised, clean
`uv run` + `npm run dev` demo.
