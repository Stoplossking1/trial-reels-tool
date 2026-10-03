"""ffprobe/ffmpeg helpers, input validation (R2) and audio loading."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

from . import config as C
from .errors import InputRejected

HDR_TRANSFERS = {"arib-std-b67", "smpte2084"}


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, capture_output=True, **kw)
    if p.returncode != 0:
        tail = (p.stderr or b"")[-2000:].decode(errors="replace")
        raise RuntimeError(f"{cmd[0]} failed ({p.returncode}): {tail}")
    return p


def ffprobe(path: str | Path) -> dict:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True,
    )
    if p.returncode != 0:
        return {}
    return json.loads(p.stdout or b"{}")


def _rotation(stream: dict) -> int:
    for sd in stream.get("side_data_list", []) or []:
        if "rotation" in sd:
            return int(round(float(sd["rotation"])))
    tag = (stream.get("tags") or {}).get("rotate")
    return int(tag) if tag else 0


@dataclass
class MediaInfo:
    path: str
    width: int          # as displayed, after rotation
    height: int
    duration: float
    fps: float
    has_audio: bool
    hdr: bool
    size_bytes: int

    def to_dict(self) -> dict:
        return asdict(self)


def validate(path: str | Path) -> MediaInfo:
    """Return MediaInfo or raise InputRejected with the plain message from the spec (design 1.2)."""
    path = Path(path)
    size = path.stat().st_size
    if size > C.MAX_BYTES:
        raise InputRejected("too_big", "This video is over 500 MB.")
    info = ffprobe(path)
    fmt = (info.get("format") or {}).get("format_name", "")
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"
                  and not (s.get("disposition") or {}).get("attached_pic")), None)
    if not info or video is None or not ({"mov", "mp4"} & set(fmt.split(","))):
        raise InputRejected("bad_format", "This file isn't a video we can read. Upload an MOV or MP4.")
    w, h = int(video["width"]), int(video["height"])
    if abs(_rotation(video)) % 180 == 90:
        w, h = h, w
    if w >= h:
        raise InputRejected("sideways", "This video is sideways. Upload a vertical one.")
    if abs((w / h) / (9 / 16) - 1) > C.ASPECT_TOLERANCE:
        raise InputRejected("not_9_16", "This video isn't 9:16. Upload a full-screen vertical video.")
    dur = float((info.get("format") or {}).get("duration") or video.get("duration") or 0)
    if dur < C.MIN_S:
        raise InputRejected("too_short", "This video is too short. Use at least 5 seconds.")
    has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    if not has_audio:
        raise InputRejected("silent", "We can't hear anyone talking in this video. The tool needs a spoken video.")
    num, _, den = (video.get("avg_frame_rate") or "30/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 30.0
    return MediaInfo(str(path), w, h, dur, fps, has_audio, video.get("color_transfer") in HDR_TRANSFERS, size)


# ---------------------------------------------------------------- audio

SR = 16000
FRAME_S = 0.01


def load_audio(path: str | Path, start: float = 0.0, dur: float | None = None, sr: int = SR) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}"]
    if dur is not None:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    return np.frombuffer(run(cmd).stdout, dtype=np.float32)


def frame_db(samples: np.ndarray, sr: int = SR, frame_s: float = FRAME_S) -> np.ndarray:
    n = int(sr * frame_s)
    k = len(samples) // n
    if k == 0:
        return np.array([-120.0])
    fr = samples[: k * n].reshape(k, n)
    rms = np.sqrt(np.mean(fr.astype(np.float64) ** 2, axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-6))


def quiet_threshold(db: np.ndarray) -> float:
    """-40 dBFS, or noise floor + 6 dB in a noisy room, whichever is higher."""
    floor = float(np.percentile(db, 10))
    return max(C.QUIET_DB, floor + 6.0)


def is_silent(path: str | Path) -> bool:
    """Cheap check before paying for a transcript: no frame anywhere louder than -45 dBFS."""
    db = frame_db(load_audio(path))
    return float(db.max()) < -45.0


def write_wav(path: str | Path, out: str | Path) -> Path:
    run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR), str(out)])
    return Path(out)


def has_filter(name: str) -> bool:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
    return any(line.split()[1:2] == [name] for line in p.stdout.splitlines() if len(line.split()) > 1)


def env(name: str) -> str | None:
    v = os.environ.get(name)
    return v or None
