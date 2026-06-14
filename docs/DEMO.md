# 🎬 Demo Video Script (3:00) + Slide Outline

> **Live dry-run completed 2026-06-14 on the deployed app** (`https://web-production-26f2e.up.railway.app`,
> `SIMULATION=0`, real AI/ML API + Featherless). Actual numbers from that run (use these — they're real,
> not placeholders): **exposure 94/100 → REJECT**, Compliance **VETO → re-plan → FAIL again**,
> Audit Chain **"✓ chain valid · 27 entries · root fafc544f7eaa41ab…"**. Screenshots saved in this
> folder: `demo-01-dashboard.png`, `demo-02-coordinating.png` (VETO/replan visible), `demo-03-final.png`
> (94/100 REJECT), `demo-04-sealed-verified.png` (sealed + verified chain).

## Video script (target 3:00 — under lablab.ai limits)

**[0:00–0:20] Hook (problem)**
> "Every enterprise contract goes through Legal, Risk, Finance and Compliance. Today that's days of
> email threads with no audit trail. Watch four AI agents do it in under a minute — coordinating
> entirely through **Band** — while a human keeps the only key."

**[0:20–0:40] The War Room**
- Show the dashboard (`demo-01-dashboard.png`). Point at the five agent lanes. Click **Run Review**
  on the sample vendor MSA.
- "The Coordinator just opened a Band room, discovered its peers with `lookup_peers`, and recruited
  the four specialists with `add_participant`."

**[0:40–1:30] Live coordination (the heart)**
- Narrate the transcript as it streams (`demo-02-coordinating.png`):
  - "**Legal** posts 5 redlines — uncapped liability §8.2, broad indemnity §8.1, no DPA §6.1 — each
    with a **cited clause**, then `@mentions` **Risk**."
  - "**Risk** scores it **high, ~$1,000,000 exposure**, hands to **Finance**."
  - "**Finance** confirms a **$1,000,000 worst case**, hands to **Compliance**."
  - "**Compliance** — running on **Featherless** open-source inference — finds personal-data
    processing with no DPA and **VETOES**."
- "That veto isn't the end — it forces the Coordinator into a **re-plan loop**. Compliance
  re-checks and still fails, so the verdict stands. This is real coordination, not a pipeline."
  (point at the `replan` event)

**[1:30–2:10] Exposure + the human gate**
- "The Coordinator aggregates a single **exposure score: 94 / 100 — REJECT recommended**"
  (`demo-03-final.png`).
- "But no agent decides. **The human holds the only key.**" Click **Reject**.
- "Sealed."

**[2:10–2:45] The audit trail (no black box)**
- Click **Verify** (`demo-04-sealed-verified.png`). "Every message, event and the human decision is
  in a **SHA-256 hash chain** — 27 entries, chain valid, sealed root `fafc544f...`. Edit any entry
  and verification breaks — a defensible record for regulators."

**[2:45–3:00] Close**
- "Four specialized agents, coordinating through Band, with a human gate and a tamper-evident trail.
  Built with AI/ML API and Featherless. That's the Contract Redline War Room."

## Recording checklist
- [ ] Open `https://web-production-26f2e.up.railway.app` (live prod, `SIMULATION=0`, real partner
      calls — badges increment on camera).
- [ ] Browser zoomed to ~110% for readability; close other tabs/notifications.
- [ ] One clean take: Run Review → narrate transcript as it streams (~15-20s for the full chain
      incl. VETO/replan) → click Reject → click Verify.
- [ ] Screen + mic; 1080p; keep under the platform's max length (3:00).
- [ ] Recording tools (Windows): **Win+G** (Xbox Game Bar, built-in, no install) or **OBS Studio**
      (free, more control). Record screen + mic together.

---

## Slide outline (6 slides)

1. **Title** — Contract Redline War Room · Band of Agents · Track 3 · names + logo strip
   (Band, AI/ML API, Featherless).
2. **Problem** — cross-functional contract review = days, no audit trail, costly misses.
3. **Solution + architecture diagram** — the Band-room diagram from the README.
4. **Why Band is core** — the 5 platform-tool mapping table; "remove Band → it stops."
5. **Differentiators** — clause citations · Compliance veto → re-plan · human gate · hash-chained
   audit (verifiable). Partner usage: AI/ML API + Featherless.
6. **Demo + impact** — screenshot, exposure 85/REJECT, "days → minutes, defensible record," call to
   action / repo link.
