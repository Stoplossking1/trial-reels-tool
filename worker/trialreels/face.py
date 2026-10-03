"""Face, mouth, eyes and hands over time (MediaPipe), sampled at 10 fps of the source.

Boxes are normalised (0..1) in source-frame coordinates; plan.py maps them into each version's
output frame (mirror + zoom), so every check runs on exact geometry.
"""
from __future__ import annotations

import json
import subprocess
import urllib.request
from dataclasses import dataclass, asdict, field
from pathlib import Path

import cv2
import numpy as np

SAMPLE_FPS = 10
SW, SH = 360, 640  # analysis size
CACHE = Path.home() / ".cache" / "trialreels"
MODELS = {
    "face": "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
    "hand": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
}

Box = tuple[float, float, float, float]  # x0, y0, x1, y1 normalised


@dataclass
class Sample:
    t: float
    face: Box | None
    hands: list[Box] = field(default_factory=list)
    jaw_open: float = 1.0     # 0 closed .. 1 wide open
    blink: float = 1.0        # 0 eyes open .. 1 closed
    sharpness: float = 0.0    # variance of Laplacian on the face area


@dataclass
class Track:
    samples: list[Sample]

    def between(self, t0: float, t1: float) -> list[Sample]:
        """Every sample in [t0, t1], plus the nearest one on each side, so short spans are covered."""
        inside = [s for s in self.samples if t0 <= s.t <= t1]
        before = [s for s in self.samples if s.t < t0][-1:]
        after = [s for s in self.samples if s.t > t1][:1]
        return before + inside + after

    def all_boxes(self) -> list[Box]:
        out = []
        for s in self.samples:
            if s.face:
                out.append(s.face)
            out.extend(s.hands)
        return out

    def median_face_center(self) -> tuple[float, float]:
        faces = [s.face for s in self.samples if s.face]
        if not faces:
            return 0.5, 0.4
        a = np.array(faces)
        return float(np.median((a[:, 0] + a[:, 2]) / 2)), float(np.median((a[:, 1] + a[:, 3]) / 2))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps([asdict(s) for s in self.samples]))

    @classmethod
    def load(cls, path: str | Path) -> "Track":
        return cls([Sample(d["t"], tuple(d["face"]) if d["face"] else None, [tuple(h) for h in d["hands"]],
                           d["jaw_open"], d["blink"], d["sharpness"]) for d in json.loads(Path(path).read_text())])


def _model(name: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{name}_landmarker.task"
    if not p.exists():
        urllib.request.urlretrieve(MODELS[name], p)
    return str(p)


def frames(video: str | Path, fps: int = SAMPLE_FPS):
    """Yield (t, rgb uint8 SHxSWx3) at `fps`, rotation applied."""
    cmd = ["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps},scale={SW}:{SH}",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = SW * SH * 3
    i = 0
    try:
        while True:
            buf = p.stdout.read(n)
            if len(buf) < n:
                break
            yield i / fps, np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
            i += 1
    finally:
        p.stdout.close()
        p.wait()


def _box(landmarks) -> Box:
    xs = [p.x for p in landmarks]
    ys = [p.y for p in landmarks]
    return (max(0.0, min(xs)), max(0.0, min(ys)), min(1.0, max(xs)), min(1.0, max(ys)))


def _crops() -> list[tuple[int, int]]:
    """Square windows (top row, bottom row) over the tall frame: top, middle, bottom.

    The face detector squeezes its input to a small square, so a face in a full 9:16 frame is often too small
    to find. Looking at square sections keeps the face large enough.
    """
    return [(0, SW), ((SH - SW) // 2, (SH + SW) // 2), (SH - SW, SH)]


def _detect_face(face_lm, mp, rgb: np.ndarray, order: list[int]):
    """Returns (crop index, landmarks in full-frame normalised coords, blendshapes) or None."""
    for ci in order:
        y0, y1 = _crops()[ci]
        sub = np.ascontiguousarray(rgb[y0:y1])
        r = face_lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=sub))
        if r.face_landmarks:
            pts = [(p.x, (y0 + p.y * (y1 - y0)) / SH) for p in r.face_landmarks[0]]
            return ci, pts, r.face_blendshapes[0]
    return None


def track(video: str | Path) -> Track:
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision

    face_lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=_model("face")), num_faces=1, output_face_blendshapes=True))
    hand_lm = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=_model("hand")), num_hands=2))
    out: list[Sample] = []
    last = 0
    with face_lm, hand_lm:
        for t, rgb in frames(video):
            hands = []
            for y0, y1 in _crops()[::2]:  # top and bottom squares cover the whole frame
                hr = hand_lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb[y0:y1])))
                for h in hr.hand_landmarks:
                    hands.append(_box([_P(p.x, (y0 + p.y * (y1 - y0)) / SH) for p in h]))
            s = Sample(t, None, hands)
            found = _detect_face(face_lm, mp, rgb, [last] + [i for i in range(3) if i != last])
            if found:
                last, pts, blend = found
                s.face = _box([_P(x, y) for x, y in pts])
                bs = {c.category_name: c.score for c in blend}
                s.jaw_open = float(bs.get("jawOpen", 1.0))
                s.blink = float(max(bs.get("eyeBlinkLeft", 1.0), bs.get("eyeBlinkRight", 1.0)))
                x0, y0, x1, y1 = s.face
                crop = cv2.cvtColor(rgb[int(y0 * SH):int(y1 * SH) + 1, int(x0 * SW):int(x1 * SW) + 1], cv2.COLOR_RGB2GRAY)
                s.sharpness = float(cv2.Laplacian(crop, cv2.CV_64F).var()) if crop.size else 0.0
            out.append(s)
    return Track(out)


@dataclass
class _P:
    x: float
    y: float
