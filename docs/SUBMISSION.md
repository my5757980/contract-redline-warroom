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
- **Cover Image:** `docs/warroom-demo.png` (or `docs/demo-03-final.png`).
- **Video Presentation:** [`docs/demo-video.mp4`](demo-video.mp4) — 2:12, narrated, recorded against
  the live Railway deployment (real Band + AI/ML API + Featherless calls).
- **Slide Presentation:** [`docs/slides.pdf`](slides.pdf) — 6 slides per the outline in `docs/DEMO.md`.

## 💻 App Hosting & Code Repository
- **Public GitHub Repository:** https://github.com/my5757980/contract-redline-warroom (MIT, no
  secrets committed — `.env` and `agent_config.yaml` are git-ignored).
- **Demo Application URL (live):** https://web-production-26f2e.up.railway.app
  (Railway, `SIMULATION=0`, real Band + AI/ML API + Featherless).

## Pre-submit verification (acceptance — from the spec)
- [x] Band transcript shows ≥4 agents with real @mention handoffs (✓ Coordinator+Legal+Risk+Finance+Compliance).
- [x] Compliance veto → Coordinator re-plan loop is visible (✓ verified live, 2026-06-14).
- [x] Every redline/risk finding carries a clause citation (✓).
- [x] Final status set only after explicit human action (✓ human gate — Reject sealed).
- [x] `GET /api/verify/{id}` matches the sealed root hash (✓ 27 entries, "chain valid").
- [x] AI/ML API + Featherless both exercised (real keys live; `/api/health` shows 0% stub usage).
- [x] Clean run on live URL: open Railway app → Run Review → full pipeline completes (✓).
- [x] LICENSE present (MIT) and original work.

## Partner free credits to claim before recording
- **Band Pro** — promo code `BANDHACK26` (band.ai → Manage Billing → Pro → Add promotion code).
- **AI/ML API** — claim `$10` via lablab.ai coupon page.
- **Featherless** — `$25`, promo code `BOA26`.
