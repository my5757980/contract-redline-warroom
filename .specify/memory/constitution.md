# Contract Redline War Room Constitution

**Hackathon:** Band of Agents Hackathon (lablab.ai) — Track 3: Regulated & High-Stakes Workflows
**Owner:** Muhammad Yaseen

## Mission

Build a **regulated, multi-agent contract review desk** where at least **four specialized AI agents
collaborate _through_ Band** to redline an inbound commercial contract, quantify financial and legal
exposure, check policy/compliance, and produce an **approval packet that no agent can sign alone** —
every material action gated by a human and recorded in a **sealed, tamper-evident audit trail**.

If Band were removed, the system must stop working. Band is the **collaboration layer**, not a
notification wrapper.

## Core Principles

### I. Band Is the Coordination Layer (NON-NEGOTIABLE)
All inter-agent context exchange, task handoff, state changes, and agent discovery MUST flow through
Band primitives (`thenvoi_send_message`, `thenvoi_send_event`, `thenvoi_lookup_peers`,
`thenvoi_add_participant`, `thenvoi_create_chatroom`). Direct calls between agents that bypass Band
are FORBIDDEN. The Band room transcript is the single source of truth for the review.

### II. Minimum Three, We Ship Four+ Specialized Agents
At least four distinct, single-responsibility agents — **Legal**, **Risk**, **Finance**,
**Compliance** — plus a **Coordinator** that opens the room, recruits peers, and drives the workflow.
Each agent has a narrow charter and only speaks to its specialty.

### III. Human Holds the Only Key (Human-in-the-Loop)
No contract is ever marked Approved/Rejected by an agent. Agents produce a recommendation; a **human
reviewer** issues the final, irreversible decision through an explicit approval gate — mirroring how
regulated enterprises actually sign off (legal, finance, compliance).

### IV. Everything Is Auditable (Tamper-Evident)
Every agent message, event, tool call, and human decision is appended to a **hash-chained audit log**
(each entry references the prior entry's hash). The final decision yields a **sealed audit hash** that
proves the reasoning trail was not altered. No black box.

### V. Evidence-Grounded, No Hallucinated Clauses
Agents must cite the specific contract clause/section they react to. A redline or risk flag without a
citation to source text is invalid and is rejected by the Coordinator.

### VI. Smallest Viable, Demoable Slice
Optimize for a crisp end-to-end demo: one real contract flows ingest → 4-agent Band collaboration →
human gate → sealed packet, visualized live in a War Room UI. No unrelated scope.

### VII. Secrets Never Committed
All keys (Band, AI/ML API, Featherless, Anthropic/OpenAI) live in `.env` / `agent_config.yaml`, both
git-ignored. No secret is ever hardcoded or printed to logs.

## Technology Constraints (Locked)

- **Agent runtime:** Python 3.12 + `uv` (never pip).
- **Band SDK:** `band-sdk` (`thenvoi`) with `claude_sdk` / `anthropic` adapter (Claude-powered agents),
  `langgraph` where a graph helps.
- **Partner models:** **AI/ML API** as the primary reasoning/orchestration gateway (Best Use of AI/ML
  API); **Featherless AI** for serverless open-source inference on a specialist path (Best Use of
  Featherless AI).
- **Backend:** FastAPI (audit service + Band event bridge + WebSocket to UI).
- **Frontend:** Next.js 15 + Tailwind — the "War Room" (live room, exposure dashboard, approve/veto,
  audit-chain viewer).
- **Storage:** SQLite (audit chain + contracts) for demo simplicity; no external DB dependency.

## Judging Alignment

| Judging Criterion | Principle that earns it |
|---|---|
| Application of Technology (Band as coordination layer) | I, II, V |
| Presentation (workflow easy to understand) | VI + War Room UI |
| Business Value (real enterprise problem) | III, IV (regulated sign-off + audit) |
| Originality (beyond single-agent / linear) | II, V (peer discovery, citations, veto/re-plan) |

## Governance

Constitution supersedes ad-hoc decisions. Any change to Principles I–IV requires an ADR under
`history/adr/`. Every user prompt is recorded as a PHR under `history/prompts/`. **Definition of Done:**
end-to-end demo runs; Band transcript shows ≥4 agents with real handoffs; human gate enforced; audit
hash verifies; both partner APIs demonstrably used.

**Version**: 1.0.0 | **Ratified**: 2026-06-13 | **Last Amended**: 2026-06-13
