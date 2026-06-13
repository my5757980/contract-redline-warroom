# Tasks — Contract Redline War Room

**Feature:** 001-contract-redline-warroom | **Date:** 2026-06-13
Ordered, dependency-aware. `[P]` = parallelizable.

---

## Phase 0 — Foundation
- [ ] T001 — Repo scaffolding: `agents/`, `backend/`, `web/`, `samples/`; `pyproject.toml` (uv),
  `.env.example`, `agent_config.example.yaml`, `.gitignore`, `LICENSE` (MIT), `README.md` stub.
- [ ] T002 — Add `band-sdk[anthropic,langgraph]`, `fastapi`, `uvicorn`, `websockets`, `pydantic`,
  `python-dotenv`, `pyyaml`, `httpx`, `pypdf` to project via `uv add`.
- [ ] T003 — `agents/common/audit.py`: hash-chain primitives (`append_entry`, `seal`, `verify`) over
  SQLite. Unit-testable, no Band dependency.

## Phase 1 — Band Integration Core
- [ ] T010 — `agents/common/band_client.py`: wrap `thenvoi.Agent.create` + adapter; helpers to
  `send_message(@mention)`, `send_event(structured)`, `lookup_peers`, `add_participant`,
  `create_chatroom`. Mirror every outbound/inbound to audit log.
- [ ] T011 — `agents/common/llm.py`: model router. Primary = **AI/ML API** (OpenAI-compatible base
  URL via `langchain_openai.ChatOpenAI(base_url=...)`); specialist path = **Featherless AI**;
  deterministic fallback stub. Records provider used per call (for partner-prize evidence).
- [ ] T012 — `agents/common/contract.py`: ingest PDF/text → clause chunks (`section`, `text`); helper
  `cite(section)` returns quoted source for the citation rule.

## Phase 2 — The Agents (each = single responsibility, talks only via Band)
- [ ] T020 [P] — `agents/legal.py`: tools `redline_clause(section, issue, suggested)`; emits redline
  events with citation. Charter prompt = legal counsel.
- [ ] T021 [P] — `agents/risk.py`: tool `score_risk(section, severity, exposure_usd)`; reads Legal
  redlines from room; emits risk events.
- [ ] T022 [P] — `agents/finance.py`: tool `compute_exposure(payment_terms, caps, penalties)`; emits
  finance events with worst-case $.
- [ ] T023 [P] — `agents/compliance.py`: tool `check_policy(section)` (Featherless-backed classifier)
  → PASS/FAIL + required addenda; may emit `VETO` event. Policy library in `samples/policies.md`.
- [ ] T024 — `agents/coordinator.py`: opens room (`create_chatroom`), `lookup_peers` + `add_participant`
  for the 4 specialists, sequences workflow via @mentions, enforces citation rule (rejects uncited),
  handles Compliance veto → re-plan loop, aggregates exposure score + redline list, posts final packet
  event, requests human gate.
- [ ] T025 — `agents/run_all.py`: supervisor that launches all 5 agents (`asyncio.gather`).

## Phase 3 — Backend (Audit/Bridge + API)
- [ ] T030 — FastAPI app `backend/main.py`: observer agent joins room, mirrors events to audit;
  SQLite models (contracts, clauses, reviews, audit_entries).
- [ ] T031 — REST: `POST /api/contracts`, `POST /api/reviews`, `GET /api/reviews/{id}`,
  `GET /api/audit/{id}`, `POST /api/decision` (seals root hash), `GET /api/verify/{id}`.
- [ ] T032 — `WS /ws/reviews/{id}`: stream live `{type, agent, payload, hash}` to UI.
- [ ] T033 — Replay mode (`REPLAY=1`): reconstruct + stream a past review from the audit log.

## Phase 4 — War Room UI (Next.js 15 + Tailwind)
- [ ] T040 — Scaffold `web/` (Next 15 App Router, Tailwind, dark "war room" theme).
- [ ] T041 — Upload + start review screen; lists clauses.
- [ ] T042 — Live Room panel: per-agent lanes showing messages/events + handoff arrows (WS).
- [ ] T043 — Exposure dashboard (score gauge + worst-case $) and Redline list with clause citations.
- [ ] T044 — Audit chain viewer (entries + hashes) + `Verify` button (calls `/api/verify`).
- [ ] T045 — Human gate controls: Approve / Reject / Request-Changes → `POST /api/decision`.

## Phase 5 — Demo & Submission
- [ ] T050 — `samples/`: one realistic vendor MSA contract + `samples/policies.md`; a recorded replay.
- [ ] T051 — README: architecture diagram, Band-usage mapping, partner-API mapping, run instructions.
- [ ] T052 — 3-min demo video script + slide outline.
- [ ] T053 — Submission checklist for lablab.ai (title, descriptions, tags, cover, video, repo, URL).

## Acceptance (from spec §9)
- [ ] ≥4 agents in Band transcript with real handoffs; visible veto/re-plan.
- [ ] Every finding cites a clause; human gate enforced; `verify` matches sealed hash.
- [ ] AI/ML API + Featherless both exercised (evidence in audit + README).
- [ ] `uv run agents/run_all.py` + `uvicorn backend.main:app` + `npm run dev` → end-to-end demo.

## Dependencies
T001→T002→T003 ; T010,T011,T012 require T002 ; T020-T024 require T010-T012 ; T024 requires T020-T023 ;
T025 requires T020-T024 ; T030-T033 require T010/T003 ; T040-T045 require T030-T032 ; Phase 5 requires
Phases 2–4.
