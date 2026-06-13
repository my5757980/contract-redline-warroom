# 🎬 Demo Video Script (3:00) + Slide Outline

## Video script (target 3:00 — under lablab.ai limits)

**[0:00–0:20] Hook (problem)**
> "Every enterprise contract goes through Legal, Risk, Finance and Compliance. Today that's days of
> email threads with no audit trail. Watch four AI agents do it in two minutes — coordinating
> entirely through **Band** — while a human keeps the only key."

**[0:20–0:40] The War Room**
- Show the dashboard. Point at the five agent lanes. Click **Run Review** on the sample vendor MSA.
- "The Coordinator just opened a Band room, discovered its peers with `lookup_peers`, and recruited
  the four specialists with `add_participant`."

**[0:40–1:30] Live coordination (the heart)**
- Narrate the transcript as it streams:
  - "**Legal** posts redlines — uncapped liability §8.2, auto-renewal §3.1 — each with a **cited
    clause**, then `@mentions` **Risk**."
  - "**Risk** scores it high, ~$500K exposure, hands to **Finance**."
  - "**Finance** computes a $740K worst case, hands to **Compliance**."
  - "**Compliance** — running on **Featherless** open-source inference — finds personal-data
    processing with no DPA and **VETOES**."
- "That veto isn't the end — it forces the Coordinator into a **re-plan loop**. This is real
  coordination, not a pipeline." (point at the replan event)

**[1:30–2:10] Exposure + the human gate**
- "The Coordinator aggregates a single **exposure score: 85 / 100 — REJECT recommended**."
- "But no agent decides. **The human holds the only key.**" Click **Reject**.
- "Sealed."

**[2:10–2:45] The audit trail (no black box)**
- Click **Verify**. "Every message, event and the human decision is in a **SHA-256 hash chain**.
  23 entries, chain valid, here's the sealed root hash. Edit any entry and verification breaks —
  a defensible record for regulators."

**[2:45–3:00] Close**
- "Four specialized agents, coordinating through Band, with a human gate and a tamper-evident trail.
  Built with AI/ML API and Featherless. That's the Contract Redline War Room."

## Recording checklist
- [ ] `SIMULATION=1`, server running, browser at `http://127.0.0.1:8000`, zoomed for readability.
- [ ] (Optional) add real `AIML_API_KEY` + `FEATHERLESS_API_KEY` so partner badges increment on camera.
- [ ] One clean take of: Run → watch transcript → Verify → Reject.
- [ ] Screen + mic; 1080p; keep under the platform's max length.

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
