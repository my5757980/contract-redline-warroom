"""Build a narrated demo video (mp4) from the live-run screenshots.

Offline TTS (Windows SAPI via pyttsx3) + direct ffmpeg (no moviepy, which
deadlocks on subprocess pipes in this non-interactive shell). Output:
docs/demo-video.mp4.
"""
import os
import subprocess
import textwrap
import wave

import pyttsx3
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

DOCS = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(DOCS, "_video_build")
os.makedirs(BUILD, exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SEGMENTS = [
    ("demo-01-dashboard.png",
     "Every enterprise contract goes through Legal, Risk, Finance, and Compliance. "
     "Today, that's days of email threads with no audit trail. Watch four A.I. agents "
     "do it in under a minute, coordinating entirely through Band, while a human keeps "
     "the only key."),
    ("demo-01-dashboard.png",
     "This is the Contract Redline War Room. Five agent lanes: Coordinator, Legal, "
     "Risk, Finance, and Compliance. Clicking Run Review starts the Coordinator, which "
     "opens a Band room, discovers its peers with lookup peers, and recruits the four "
     "specialists with add participant."),
    ("demo-02-coordinating.png",
     "Legal posts five redlines, including uncapped liability in section eight point "
     "two and a missing data processing agreement in section six point one, each with "
     "a cited clause, then mentions Risk. Risk scores it high, about one million dollars "
     "exposure, and hands off to Finance. Finance confirms a one million dollar worst "
     "case and hands to Compliance. Compliance, running on Featherless open source "
     "inference, finds personal data processing with no D.P.A., and vetoes. That veto "
     "triggers a Coordinator re-plan loop. Compliance re-checks and still fails, so the "
     "verdict stands. This is real coordination, not a fixed pipeline."),
    ("demo-03-final.png",
     "The Coordinator aggregates everything into a single exposure score: ninety four "
     "out of one hundred, recommendation REJECT. But no agent makes the final call. "
     "The human holds the only key. Clicking Reject seals the decision."),
    ("demo-04-sealed-verified.png",
     "Clicking Verify checks the SHA two fifty six hash chain: twenty seven entries, "
     "chain valid, sealed root fafc five four four f. Edit any entry and verification "
     "breaks, giving regulators a defensible record."),
    ("demo-04-sealed-verified.png",
     "Four specialized agents, coordinating through Band, with a human gate and a "
     "tamper-evident audit trail. Built with A.I. M.L. A.P.I. and Featherless. This is "
     "the Contract Redline War Room."),
]

CANVAS = (1280, 720)
IMG_AREA_H = 540
CAPTION_BG = (18, 20, 30)
CAPTION_FG = (235, 235, 245)


def make_frame(img_path, caption, idx):
    canvas = Image.new("RGB", CANVAS, (10, 12, 20))
    img = Image.open(os.path.join(DOCS, img_path)).convert("RGB")
    scale = min((CANVAS[0] - 40) / img.width, (IMG_AREA_H - 20) / img.height)
    new_size = (int(img.width * scale), int(img.height * scale))
    img = img.resize(new_size, Image.LANCZOS)
    x = (CANVAS[0] - new_size[0]) // 2
    y = 10
    canvas.paste(img, (x, y))

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, IMG_AREA_H, CANVAS[0], CANVAS[1]], fill=CAPTION_BG)
    font = ImageFont.truetype("arial.ttf", 24)
    wrapped = textwrap.fill(caption, width=92)
    draw.multiline_text((40, IMG_AREA_H + 18), wrapped, fill=CAPTION_FG, font=font, spacing=8)

    out = os.path.join(BUILD, f"frame_{idx:02d}.png")
    canvas.save(out)
    return out


def wav_duration(path):
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def run_ffmpeg(args):
    proc = subprocess.run(
        [FFMPEG, "-y", *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])


def main():
    seg_videos = []
    for i, (img_path, text) in enumerate(SEGMENTS):
        wav = os.path.join(BUILD, f"seg_{i:02d}.wav")
        if not os.path.exists(wav):
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            for v in engine.getProperty("voices"):
                if "David" in v.name:
                    engine.setProperty("voice", v.id)
                    break
            engine.save_to_file(text, wav)
            engine.runAndWait()
            engine.stop()
        dur = wav_duration(wav) + 0.5
        print(f"segment {i}: audio {dur:.1f}s")

        frame_path = make_frame(img_path, text, i)
        seg_out = os.path.join(BUILD, f"seg_{i:02d}.mp4")
        run_ffmpeg([
            "-loop", "1", "-i", frame_path,
            "-i", wav,
            "-t", f"{dur:.2f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100",
            "-vf", "fps=24",
            seg_out,
        ])
        seg_videos.append(seg_out)
        print(f"  -> {seg_out}")

    list_path = os.path.join(BUILD, "concat.txt")
    with open(list_path, "w", encoding="utf-8") as fh:
        for sv in seg_videos:
            fh.write(f"file '{sv}'\n")

    out_path = os.path.join(DOCS, "demo-video.mp4")
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", out_path])
    print("DONE", out_path)


if __name__ == "__main__":
    main()
