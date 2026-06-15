"""Generate the 6-slide pitch deck (PNG frames + slides.pdf) for lablab.ai submission.

Matches the outline in docs/DEMO.md. Output: docs/slides.pdf + docs/_slides/slide_0N.png
"""
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.pagesizes import landscape

DOCS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DOCS, "_slides")
os.makedirs(OUT, exist_ok=True)

W, H = 1280, 720
BG = (10, 14, 26)
PANEL = (30, 41, 59)
TEXT = (230, 237, 246)
ACCENT = (56, 189, 248)
MUTED = (148, 163, 184)
GOOD = (52, 211, 153)
BAD = (248, 113, 113)


def font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(name, size)


def base_slide(footer_left="Contract Redline War Room", footer_right=""):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 50, W, H], fill=PANEL)
    d.text((40, H - 38), footer_left, font=font(18), fill=MUTED)
    if footer_right:
        w = d.textlength(footer_right, font=font(18))
        d.text((W - 40 - w, H - 38), footer_right, font=font(18), fill=MUTED)
    return img, d


def wrap(d, text, fnt, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def bullets(d, items, x, y, fnt, gap=46, max_width=1100, color=TEXT, bullet="›"):
    for item in items:
        lines = wrap(d, item, fnt, max_width - 50)
        d.text((x, y), bullet, font=fnt, fill=ACCENT)
        for j, line in enumerate(lines):
            d.text((x + 50, y + j * (fnt.size + 8)), line, font=fnt, fill=color)
        y += max(1, len(lines)) * (fnt.size + 8) + (gap - fnt.size)
    return y


# ── Slide 1: Title ───────────────────────────────────────────────────────
img, d = base_slide(footer_left="Band of Agents Hackathon · lablab.ai · Track 3")
d.rounded_rectangle([90, 165, 110, 220], radius=4, fill=ACCENT)
d.text((130, 150), "Contract Redline War Room", font=font(64, True), fill=TEXT)
for i, line in enumerate(wrap(d, "Four specialized AI agents collaborate through Band to redline a "
                                  "contract, quantify exposure, and assemble a human-gated approval "
                                  "packet — sealed in a tamper-evident audit trail.",
                               font(28), 1040)):
    d.text((90, 250 + i * 42), line, font=font(28), fill=MUTED)
d.text((90, 440), "Track 3 — Regulated & High-Stakes Workflows", font=font(26, True), fill=ACCENT)
d.text((90, 500), "Built with  Band  ·  AI/ML API  ·  Featherless AI", font=font(26), fill=TEXT)
d.text((90, 560), "Muhammad Yaseen", font=font(22), fill=MUTED)
img.save(os.path.join(OUT, "slide_01.png"))

# ── Slide 2: Problem ─────────────────────────────────────────────────────
img, d = base_slide(footer_right="1 / 6")
d.text((90, 70), "The Problem", font=font(48, True), fill=TEXT)
bullets(d, [
    "Every inbound contract (vendor MSAs, NDAs, SOWs, DPAs) is routed through "
    "Legal, Risk, Finance and Compliance.",
    "Today that means email threads, tracked-changes docs and meetings — "
    "taking days, with no clean audit trail.",
    "Costly misses slip through: uncapped liability, auto-renewal traps, "
    "non-compliant data-processing clauses.",
    "When something goes wrong, there's no defensible record of who decided "
    "what, and why.",
], 110, 180, font(30), max_width=1080)
img.save(os.path.join(OUT, "slide_02.png"))

# ── Slide 3: Solution + architecture ────────────────────────────────────
img, d = base_slide(footer_right="2 / 6")
d.text((90, 50), "The Solution: A War Room", font=font(46, True), fill=TEXT)
d.text((90, 122), "The Coordinator opens a Band room, discovers + recruits 4 specialist agents.", font=font(24), fill=MUTED)

diagram = [
    ("Coordinator", "opens Band room · lookup_peers · add_participant", ACCENT),
    ("Legal", "redlines clauses, cites the exact source text", TEXT),
    ("Risk", "scores severity + dollar exposure", TEXT),
    ("Finance", "computes worst-case financial exposure", TEXT),
    ("Compliance", "policy check — can VETO and force a re-plan loop", BAD),
]
y = 180
row_h, step = 58, 68
for name, desc, col in diagram:
    d.rounded_rectangle([110, y, 1170, y + row_h], radius=10, fill=PANEL)
    d.ellipse([130, y + row_h // 2 - 7, 144, y + row_h // 2 + 7], fill=col)
    d.text((160, y + 14), name, font=font(26, True), fill=col)
    d.text((400, y + 17), desc, font=font(22), fill=MUTED)
    y += step

y += 6
d.text((110, y), "↓  aggregated exposure score + redline packet", font=font(24), fill=TEXT)
y += 46
d.rounded_rectangle([110, y, 1170, y + row_h], radius=10, fill=(30, 64, 50))
d.ellipse([130, y + row_h // 2 - 7, 144, y + row_h // 2 + 7], fill=GOOD)
d.text((160, y + 14), "HUMAN GATE", font=font(26, True), fill=GOOD)
d.text((400, y + 17), "Approve / Reject / Request-Changes — only a human decides", font=font(22), fill=TEXT)
img.save(os.path.join(OUT, "slide_03.png"))

# ── Slide 4: Why Band is core ───────────────────────────────────────────
img, d = base_slide(footer_right="3 / 6")
d.text((90, 60), "Why Band Is Core", font=font(48, True), fill=TEXT)
d.text((90, 140), "Every handoff, finding, state change and discovery is a real Band primitive:", font=font(26), fill=MUTED)

rows = [
    ("band_create_chatroom", "Coordinator opens the review room"),
    ("band_lookup_peers", "discovers Legal / Risk / Finance / Compliance"),
    ("band_add_participant", "recruits each specialist into the room"),
    ("band_send_message (@mention)", "every agent → agent handoff"),
    ("band_send_event", "findings, veto, exposure packet, state"),
]
y = 210
for tool, desc in rows:
    d.rounded_rectangle([110, y, 1170, y + 64], radius=10, fill=PANEL)
    d.text((140, y + 16), tool, font=font(24, True), fill=ACCENT)
    d.text((620, y + 18), desc, font=font(24), fill=TEXT)
    y += 76

d.text((90, y + 20), "Remove Band from this system → it stops working.", font=font(28, True), fill=BAD)
img.save(os.path.join(OUT, "slide_04.png"))

# ── Slide 5: Differentiators ────────────────────────────────────────────
img, d = base_slide(footer_right="4 / 6")
d.text((90, 60), "What Makes This Different", font=font(48, True), fill=TEXT)
bullets(d, [
    "Cited findings — every redline and risk score quotes the exact contract clause.",
    "Compliance can VETO — forcing a visible Coordinator re-plan loop, not a fixed pipeline.",
    "Human holds the only key — Approve / Reject / Request-Changes; no agent signs off alone.",
    "Tamper-evident audit — SHA-256 hash chain, independently verifiable via GET /api/verify/{id}.",
    "Both partners exercised live — AI/ML API (reasoning) + Featherless (compliance inference), "
    "tallied at /api/health.",
], 110, 180, font(28), max_width=1080)
img.save(os.path.join(OUT, "slide_05.png"))

# ── Slide 6: Demo + impact ──────────────────────────────────────────────
img, d = base_slide(footer_right="5 / 6")
d.text((90, 50), "Demo + Impact", font=font(48, True), fill=TEXT)

shot = Image.open(os.path.join(DOCS, "demo-03-final.png")).convert("RGB")
scale = min(620 / shot.width, 540 / shot.height)
shot = shot.resize((int(shot.width * scale), int(shot.height * scale)), Image.LANCZOS)
img.paste(shot, (90, 130))

x2 = 760
d.text((x2, 140), "Exposure Score", font=font(28), fill=MUTED)
d.text((x2, 175), "94 / 100", font=font(72, True), fill=BAD)
d.text((x2, 260), "Recommendation: REJECT", font=font(28, True), fill=BAD)

d.text((x2, 340), "Days → Minutes", font=font(34, True), fill=ACCENT)
d.text((x2, 390), "Defensible, sealed record", font=font(26), fill=TEXT)
d.text((x2, 425), "for regulators", font=font(26), fill=TEXT)

d.text((x2, 500), "Live demo:", font=font(22), fill=MUTED)
d.text((x2, 530), "web-production-26f2e.up.railway.app", font=font(22, True), fill=ACCENT)
d.text((x2, 575), "Code:", font=font(22), fill=MUTED)
d.text((x2, 605), "github.com/my5757980/contract-redline-warroom", font=font(22, True), fill=ACCENT)
img.save(os.path.join(OUT, "slide_06.png"))

# ── Assemble PDF ─────────────────────────────────────────────────────────
pdf_path = os.path.join(DOCS, "slides.pdf")
c = pdfcanvas.Canvas(pdf_path, pagesize=landscape((W, H)))
for i in range(1, 7):
    c.drawImage(os.path.join(OUT, f"slide_{i:02d}.png"), 0, 0, width=W, height=H)
    c.showPage()
c.save()
print("DONE", pdf_path)
