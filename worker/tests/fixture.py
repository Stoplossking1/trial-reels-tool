"""Builds a synthetic talking-head clip + matching transcript for tests.

Picture: the public-domain NASA astronaut portrait from scikit-image, on a 1080x1920 frame.
Sound: one tone burst per word, at the times in the transcript, with real silence between.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

SCRIPT = [
    "3 apps I stopped paying for this year.",
    "Canva was costing me 40 dollars a month.",
    "Here is how to replace it for free.",
    "Why are you still paying for this?",
    "Stop wasting money on tools you never use.",
]
SR = 48000


def words_with_times(lead_in: float = 0.6, word_s: float = 0.28, gap_s: float = 0.07, sentence_gap: float = 0.45):
    t = lead_in
    out = []
    for sent in SCRIPT:
        for w in sent.split():
            out.append({"text": w, "start": round(t, 3), "end": round(t + word_s, 3)})
            t += word_s + gap_s
        t += sentence_gap
    return out, t + 0.6


def make(dirpath: Path, landscape: bool = False, seconds: float | None = None, silent: bool = False) -> tuple[Path, Path]:
    from PIL import Image, ImageFilter
    from skimage import data

    dirpath.mkdir(parents=True, exist_ok=True)
    words, dur = words_with_times()
    if seconds:
        dur = seconds
    W, H = (1920, 1080) if landscape else (1080, 1920)
    face = Image.fromarray(data.astronaut())
    bg = face.resize((W, H)).filter(ImageFilter.GaussianBlur(30))
    side = min(W, H)
    bg.paste(face.resize((side, side)), ((W - side) // 2, (H - side) // 3))
    img = dirpath / "frame.png"
    bg.save(img)

    audio = np.zeros(int(dur * SR), np.float32)
    rng = np.random.default_rng(0)
    audio += rng.normal(0, 0.0005, audio.shape).astype(np.float32)  # room tone
    if not silent:
        for w in words:
            a, b = int(w["start"] * SR), int(w["end"] * SR)
            if b > len(audio):
                break
            tt = np.arange(b - a) / SR
            env = np.sin(np.pi * np.linspace(0, 1, b - a)) ** 0.5
            tone = sum(np.sin(2 * np.pi * f * tt) / k for k, f in enumerate((180, 360, 540, 900), 1))
            audio[a:b] += (0.25 * env * tone).astype(np.float32)
    raw = dirpath / "audio.f32"
    audio.tofile(raw)

    out = dirpath / ("landscape.mp4" if landscape else "silent.mp4" if silent else f"talk_{int(dur)}s.mov")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-i", str(img),
                    "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw),
                    "-vf", f"scale={W}:{H},noise=alls=6:allf=t", "-t", f"{dur:.2f}",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)],
                   check=True)
    tr = dirpath / "transcript.json"
    tr.write_text(json.dumps({"provider": "fixture", "words": [w for w in words if w["end"] < dur]}))
    return out, tr
