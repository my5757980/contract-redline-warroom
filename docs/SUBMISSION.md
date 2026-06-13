# ✅ lablab.ai Submission Checklist — Band of Agents Hackathon

Deadline: **Jun 19, 8:00 PM PST**. Submit at the hackathon page on lablab.ai.

## 📋 Basic Information
- **Project Title:** Contract Redline War Room
- **Short Description (1 line):**
  > Four specialized AI agents coordinate through Band to redline a contract, quantify exposure, and
  > assemble a human-gated approval packet with a sealed, tamper-evident audit trail.
- **Long Description:** use `README.md` (problem → solution → Band integration → partners → audit).
- **Technology & Category Tags:** `Band`, `Codeband`/multi-agent, `AI/ML API`, `Featherless`,
  `Anthropic Claude`, `FastAPI`, `Python`, `Track 3: Regulated & High-Stakes`.

## 📸 Cover Image & Presentation
- **Cover Image:** `docs/warroom-demo.png` (or a titled variant).
- **Video Presentation:** record per `docs/DEMO.md` (≤ 3 min).
- **Slide Presentation:** build from the 6-slide outline in `docs/DEMO.md`.

## 💻 App Hosting & Code Repository
- **Public GitHub Repository:** push this repo (MIT, no secrets committed — `.env` and
  `agent_config.yaml` are git-ignored).
- **Demo Application Platform / URL:** deploy the FastAPI app (serves the UI). Options:
  - Railway (PRIMARY) or Render — `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
  - Procfile: `web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.

## Pre-submit verification (acceptance — from the spec)
- [ ] Band transcript shows ≥4 agents with real @mention handoffs (✓ Coordinator+Legal+Risk+Finance+Compliance).
- [ ] Compliance veto → Coordinator re-plan loop is visible (✓).
- [ ] Every redline/risk finding carries a clause citation (✓).
- [ ] Final status set only after explicit human action (✓ human gate).
- [ ] `GET /api/verify/{id}` matches the sealed root hash (✓ 23 entries, valid).
- [ ] AI/ML API + Featherless both exercised (add keys; badges increment; `/api/health` shows tally).
- [ ] Clean run: `uv run uvicorn backend.main:app` → open `:8000` → Run Review (✓).
- [ ] LICENSE present (MIT) and original work.

## Partner free credits to claim before recording
- **Band Pro** — promo code `BANDHACK26` (band.ai → Manage Billing → Pro → Add promotion code).
- **AI/ML API** — claim `$10` via lablab.ai coupon page.
- **Featherless** — `$25`, promo code `BOA26`.
