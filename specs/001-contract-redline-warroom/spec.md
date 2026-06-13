# Feature Spec — Contract Redline War Room

**Feature ID:** 001-contract-redline-warroom
**Status:** Draft → Ready for Plan
**Track:** 3 (Regulated & High-Stakes Workflows)
**Date:** 2026-06-13

---

## 1. Surface & Success Criteria (one sentence)

A web "War Room" where a user uploads a commercial contract and watches **four specialized AI agents
collaborate live through Band** to redline it, quantify exposure, and assemble an approval packet that
a **human signs off**, producing a **sealed, verifiable audit trail**.

## 2. Problem & Business Value

Enterprises route every inbound contract (vendor MSAs, NDAs, SOWs, DPAs) through Legal, Risk, Finance,
and Compliance — today via email threads, tracked-changes docs, and meetings that take days and leave
no clean audit trail. Mistakes (uncapped liability, auto-renewal traps, non-compliant data clauses)
are expensive. **A coordinated agent desk compresses days of cross-functional review into minutes
while producing a defensible, tamper-evident record** — exactly the kind of regulated, high-stakes
workflow Track 3 rewards.

## 3. Users

- **Reviewer (human-in-the-loop):** legal ops / deal desk operator who triggers a review and holds the
  final Approve / Reject / Request-Changes decision.
- **The 5 agents** (system actors): Coordinator, Legal, Risk, Finance, Compliance.

## 4. Core User Story

> As a deal-desk reviewer, I upload a vendor contract, watch the agents debate and hand off work
> through Band in real time, see a consolidated exposure score and a redline list with clause
> citations, and then approve or veto — after which I can download a sealed audit packet that proves
> exactly how the recommendation was reached.

## 5. The Agents (charters)

| Agent | Responsibility | Reads | Emits to Band |
|---|---|---|---|
| **Coordinator** | Opens the Band room, recruits the 4 specialists via `lookup_peers` + `add_participant`, sequences the workflow, enforces citation rule, assembles final packet, requests human gate. | full contract | task assignments, state changes, final packet event |
| **Legal** | Redlines risky clauses (liability, indemnity, IP, termination, governing law). | full contract | redline events with clause citations |
| **Risk** | Scores enterprise risk (auto-renewal, uncapped liability, data breach exposure) → numeric exposure. | contract + Legal's redlines | risk events with severity + exposure $ |
| **Finance** | Extracts payment terms, caps, penalties, computes financial exposure & worst-case. | contract + Risk findings | finance events with $ figures |
| **Compliance** | Checks against policy library (GDPR/DPA, data residency, security addendum). PASS/FAIL + required addenda. | contract + all prior findings | compliance verdict event; may **veto** → forces Coordinator re-plan |

## 6. Functional Requirements

- **FR1** — User uploads a contract (PDF or text). System ingests and chunks into clause-addressable
  sections.
- **FR2** — Coordinator creates a Band room and recruits ≥4 specialist agents through Band primitives
  (no hardcoded direct calls).
- **FR3** — Each specialist posts findings to the Band room as **events** (structured) and **@mentions**
  the next agent for handoff. All collaboration is visible in the room transcript.
- **FR4** — Every finding MUST include a clause citation (section id + quoted text). Coordinator
  rejects uncited findings back to the author.
- **FR5** — Compliance may **veto**; a veto forces the Coordinator to re-open the relevant task (visible
  re-plan loop), demonstrating real coordination — not a linear pipeline.
- **FR6** — System aggregates a **single exposure score** (0–100) + dollar worst-case + redline list.
- **FR7** — **Human gate:** the reviewer must explicitly Approve / Reject / Request-Changes. No agent
  may set the final status.
- **FR8** — Every message, event, tool call, and the human decision is appended to a **hash-chained
  audit log**; the final decision seals a **root audit hash** that can be independently verified.
- **FR9** — War Room UI shows, live: the room transcript (per-agent lanes), exposure dashboard, redline
  list, and the audit chain; plus Approve/Reject controls.
- **FR10** — **Partner usage:** AI/ML API powers agent reasoning/orchestration; Featherless AI powers a
  specialist inference path (e.g., Compliance clause-classification). Both are demonstrably exercised.

## 7. Non-Functional / Constraints

- Demo path completes in < ~3 minutes on one contract.
- Works fully online with Band's hosted platform; agents run locally via the SDK WebSocket.
- No secrets in repo; MIT license; original work.
- Graceful **degraded mode**: if live Band credentials are unavailable during judging, a recorded/replay
  mode reproduces the exact Band transcript from the sealed audit log (so the demo never hard-fails).

## 8. Out of Scope

- Multi-tenant auth / user accounts, billing, e-signature integration, production-grade contract
  storage, fine-tuned legal models. (Future work.)

## 9. Acceptance Checks

- [ ] Band room transcript shows ≥4 distinct agents with real @mention handoffs and structured events.
- [ ] At least one Compliance veto → Coordinator re-plan loop is visible.
- [ ] Every redline/risk finding carries a clause citation.
- [ ] Final status is only set after explicit human action.
- [ ] `verify_audit` recomputes the chain and matches the sealed root hash.
- [ ] AI/ML API and Featherless AI both show evidence of use (logs + README mapping).
- [ ] End-to-end demo runs from a clean `uv run` + `npm run dev`.

## 10. Risks (max 3)

1. **Band live-connection flakiness during judging** → mitigate with replay mode from the audit log.
2. **Partner API rate/credit limits** → cache responses; keep a deterministic fallback model.
3. **Scope creep on UI polish** → freeze UI to the four panels above once functional.
