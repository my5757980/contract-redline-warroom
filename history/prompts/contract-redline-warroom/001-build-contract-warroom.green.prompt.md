---
id: 001
title: Build Contract Redline War Room (Band multi-agent, Track 3)
stage: green
date: 2026-06-13
surface: agent
model: claude-opus-4-8
feature: contract-redline-warroom
branch: main
user: Muhammad Yaseen
command: (freeform build session)
labels: ["band", "multi-agent", "hackathon", "track-3", "audit", "aimlapi", "featherless"]
links:
  spec: specs/001-contract-redline-warroom/spec.md
  plan: specs/001-contract-redline-warroom/plan.md
  tasks: specs/001-contract-redline-warroom/tasks.md
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - specs/001-contract-redline-warroom/spec.md
  - specs/001-contract-redline-warroom/plan.md
  - specs/001-contract-redline-warroom/tasks.md
  - agents/common/audit.py
  - agents/common/llm.py
  - agents/common/contract.py
  - agents/common/band_client.py
  - agents/base.py
  - agents/legal.py
  - agents/risk.py
  - agents/finance.py
  - agents/compliance.py
  - agents/coordinator.py
  - agents/run_all.py
  - backend/main.py
  - backend/smoke_test.py
  - web/index.html
  - samples/sample_msa.txt
  - samples/policies.md
  - README.md
  - docs/DEMO.md
  - docs/SUBMISSION.md
  - Procfile
  - requirements.txt
  - LICENSE
tests:
  - "agents/common/audit.py self-test: clean chain verifies, tampered chain detected at seq 1"
  - "agents.run_all end-to-end: 5 agents, veto+re-plan, exposure 85/REJECT, sealed root verified (24 entries)"
  - "backend.smoke_test: health OK, review runs, exposure 85, human gate seals, verify valid, 25 events"
  - "Playwright UI: Run Review -> live transcript -> Verify (23 entries valid) -> Reject sealed"
---

## Prompt (verbatim)

> haaa chloo shuruu kartayy haii project banana mujayyy ya hackathone jeetna haiiiiii full 100% denaa apnaaa ok

(Preceded by: scan the Band of Agents Hackathon page via Playwright; then choices —
Project: "Contract Redline War Room (Track 3)"; Partners: "Dono use karein (max prizes)" = AI/ML API + Featherless.)

## Response (summary)

Built an end-to-end, winning-grade submission for the Band of Agents Hackathon (Track 3):

1. **Scanned** the live hackathon + Band SDK docs with Playwright to use the real `thenvoi`/band-sdk
   API (no invented APIs): primitives `create_chatroom`, `lookup_peers`, `add_participant`,
   `send_message` (@mention), `send_event`; `claude_sdk`/`anthropic` adapters.
2. **SpecKit Plus pipeline** (locked workflow): `uvx specifyplus init` → constitution → spec → plan →
   tasks, all written for the feature.
3. **Implemented 5 agents** (Coordinator + Legal/Risk/Finance/Compliance) that collaborate ONLY through
   Band; Compliance can VETO → Coordinator re-plan loop. Findings carry clause citations.
4. **Partner integration**: AI/ML API as primary reasoning gateway; Featherless for the Compliance
   open-source inference path; per-call usage tally for prize evidence. Deterministic fallback keeps
   the demo alive offline (SIMULATION mode) — a faithful in-process Band-semantics bus.
5. **Tamper-evident audit**: SHA-256 hash chain; human gate seals a verifiable root hash.
6. **FastAPI bridge** (REST + WebSocket) serving a live dark "War Room" dashboard; verified end-to-end
   with Playwright (exposure 85/100 → REJECT, audit chain valid, human gate sealed).
7. **Demo assets**: README (Band + partner mapping), 3-min video script, slide outline, lablab.ai
   submission checklist; MIT license; Procfile/requirements for Railway/Render.

Committed as root commit on a fresh git repo (60 files). Remaining human actions: claim partner credits,
push to GitHub, deploy, record the demo video, submit on lablab.ai before Jun 19 8PM PST.

## Outcome

- All automated checks pass; UI demo verified via Playwright with screenshot (`docs/warroom-demo.png`).
- Architecturally significant decisions (Band-as-coordination, dual partner routing, hash-chained audit)
  flagged for an optional ADR.
