"""Plan each version (design 1.5). Rendering only follows the plan, so every rule can be checked on it."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

from . import config as C
from . import overlays as O
from .face import Box, Track
from .look import Look
from .transcript import Transcript, in_word
from .writing import Hook

PAUSE_S = 0.25


# ---------------------------------------------------------------- geometry


@dataclass
class Geometry:
    """Maps source time/positions into one version's output frame."""
    look: Look
    face_center: tuple[float, float]

    @property
    def crop_w(self) -> float:
        return C.W / self.look.zoom

    @property
    def crop_h(self) -> float:
        return C.H / self.look.zoom

    @property
    def offset(self) -> tuple[float, float]:
        """Top-left of the zoom window, in unzoomed 1080x1920 pixels, centred on the face."""
        cx, cy = self.face_center
        if self.look.mirror:
            cx = 1 - cx
        ox = min(max(cx * C.W - self.crop_w / 2, 0), C.W - self.crop_w)
        oy = min(max(cy * C.H - self.crop_h / 2, 0), C.H - self.crop_h)
        return ox, oy

    def out_box(self, b: Box, pad: float = 0.0) -> tuple[float, float, float, float]:
        x0, y0, x1, y1 = b
        if self.look.mirror:
            x0, x1 = 1 - x1, 1 - x0
        x0, x1 = (x0 - pad) * C.W, (x1 + pad) * C.W
        y0, y1 = (y0 - pad) * C.H, (y1 + pad) * C.H
        ox, oy = self.offset
        z = self.look.zoom
        return ((x0 - ox) * z, (y0 - oy) * z, (x1 - ox) * z, (y1 - oy) * z)

    def in_crop(self, b: Box) -> bool:
        x0, y0, x1, y1 = self.out_box(b)
        return x0 >= -1 and y0 >= -1 and x1 <= C.W + 1 and y1 <= C.H + 1

    def out_t(self, src_t: float) -> float:
        return (src_t - self.look.trim) / self.look.speed

    def src_t(self, out_t: float) -> float:
        return out_t * self.look.speed + self.look.trim


def overlap(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


# ---------------------------------------------------------------- overlays


@dataclass
class Overlay:
    kind: str            # hook | caption
    text: str
    png: str
    x: int
    y: int
    w: int
    h: int
    t0: float            # output seconds
    t1: float
    cap_px: int

    @property
    def box(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)


def in_safe_area(box) -> bool:
    x0, y0, x1, y1 = box
    if x0 < C.SAFE_X0 or y0 < C.SAFE_Y0 or x1 > C.SAFE_X1 or y1 > C.SAFE_Y1:
        return False
    return not (y1 > C.BUTTONS_Y and x1 > C.BUTTONS_X)


def _slot(name: str, w: int, h: int) -> tuple[int, int]:
    mid = (C.W - w) // 2
    low_mid = int((C.SAFE_X0 + C.BUTTONS_X) / 2 - w / 2)
    return {
        "top": (mid, C.SAFE_Y0 + 20),
        "upper": (mid, 470),
        "above_buttons": (mid, C.BUTTONS_Y - 10 - h),
        "bottom": (low_mid, C.SAFE_Y1 - 20 - h),
    }[name]


HOOK_SLOTS = ("top", "upper", "bottom", "above_buttons")
CAPTION_SLOTS = ("above_buttons", "bottom", "top", "upper")


def face_boxes(track: Track, geo: Geometry, t0: float, t1: float) -> list:
    return [geo.out_box(s.face, C.FACE_PAD) for s in track.between(geo.src_t(t0), geo.src_t(t1)) if s.face]


def place(w: int, h: int, t0: float, t1: float, slots, track: Track, geo: Geometry) -> tuple[int, int]:
    faces = face_boxes(track, geo, t0, t1)
    best, best_hits = None, None
    for name in slots:
        x, y = _slot(name, w, h)
        box = (x, y, x + w, y + h)
        if not in_safe_area(box):
            continue
        hits = sum(overlap(box, f) for f in faces)
        if hits == 0:
            return x, y
        if best_hits is None or hits < best_hits:
            best, best_hits = (x, y), hits
    return best if best else _slot(slots[0], w, h)


# ---------------------------------------------------------------- captions


def caption_groups(t: Transcript, geo: Geometry, start_after: float, out_dur: float) -> list[tuple[str, float, float]]:
    """1-4 words per group, broken at punctuation and pauses; each shown >= 1.2 s and <= 3.5 s (output time)."""
    groups, cur = [], []
    for i, w in enumerate(t.words):
        cur.append(w)
        nxt = t.words[i + 1] if i + 1 < len(t.words) else None
        brk = (len(cur) == 4 or nxt is None or re.search(r"[.,?!;:]$", w.text)
               or (nxt and nxt.start - w.end > PAUSE_S))
        if brk:
            groups.append(cur)
            cur = []
    out = []
    prev_end = start_after
    for g in groups:
        a, b = geo.out_t(g[0].start), geo.out_t(g[-1].end)
        if b <= start_after:
            continue  # spoken while the hook is up
        a = max(a, prev_end)
        b = min(max(b, a + C.MIN_ON_SCREEN_S), a + C.LABEL_MAX_S, out_dur)
        if b - a < C.MIN_ON_SCREEN_S - 1e-6:
            continue  # no room left at the very end; never show a caption for less than 1.2 s
        out.append((" ".join(w.text for w in g), round(a, 3), round(b, 3)))
        prev_end = b
    return out


# ---------------------------------------------------------------- cover


def cover_times(t: Transcript, track: Track, n: int, max_src_t: float) -> list[float]:
    """Frames with mouth closed, eyes open, not inside a word, sharp; at least 1 s apart (R7)."""
    def ok(s, jaw, blink):
        return s.face and s.jaw_open < jaw and s.blink < blink and not in_word(t, s.t) and 0.3 < s.t < max_src_t

    for jaw, blink in ((0.08, 0.35), (0.12, 0.45), (0.2, 0.5)):
        cands = sorted((s for s in track.samples if ok(s, jaw, blink)),
                       key=lambda s: (-(s.sharpness / 100) + s.jaw_open + s.blink))
        picked: list[float] = []
        for s in cands:
            if all(abs(s.t - p) >= 1.0 for p in picked):
                picked.append(s.t)
            if len(picked) == n:
                return picked
    return picked


# ---------------------------------------------------------------- the plan


@dataclass
class VersionPlan:
    idx: int
    hook: Hook
    look: Look
    face_center: tuple[float, float]
    out_duration: float
    overlays: list[Overlay] = field(default_factory=list)
    captions_on: bool = True
    cover_src_t: float | None = None
    cover_text: str = ""
    cover_overlay: Overlay | None = None
    post_caption: str = ""
    what_changed: list[str] = field(default_factory=list)
    post_order: int = 0

    @property
    def geo(self) -> Geometry:
        return Geometry(self.look, self.face_center)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["hook"] = asdict(self.hook)
        d["look"] = self.look.to_dict()
        return d


def build(idx: int, hook: Hook, look: Look, t: Transcript, track: Track, src_dur: float,
          workdir: Path, captions_on: bool = True) -> VersionPlan | None:
    """None if the hook can't fit on screen in this look's font/style."""
    geo = Geometry(look, track.median_face_center())
    out_dur = (src_dur - look.trim) / look.speed
    vp = VersionPlan(idx, hook, look, geo.face_center, round(out_dur, 3), captions_on=captions_on)

    hook_img = O.fit_hook(hook.text, look.font, look.hook_style)
    if hook_img is None or hook_img.cap_px < C.MIN_TEXT_PX:
        return None
    a, b = t.sentences[0]
    hook_end = min(max(geo.out_t(t.words[b].end), C.HOOK_MIN_S), C.HOOK_MAX_S, out_dur)
    png = O.save(hook_img, workdir / f"v{idx}_hook.png")
    w, h = hook_img.image.size
    x, y = place(w, h, 0.0, hook_end, HOOK_SLOTS, track, geo)
    vp.overlays.append(Overlay("hook", hook.text, str(png), x, y, w, h, 0.0, round(hook_end, 3), hook_img.cap_px))

    if captions_on:
        for k, (text, c0, c1) in enumerate(caption_groups(t, geo, hook_end, out_dur)):
            ti = O.caption_image(text, look.font, look.caption_size)
            png = O.save(ti, workdir / f"v{idx}_cap{k:03d}.png")
            w, h = ti.image.size
            x, y = place(w, h, c0, c1, CAPTION_SLOTS, track, geo)
            vp.overlays.append(Overlay("caption", text, str(png), x, y, w, h, c0, c1, ti.cap_px))
    return vp


def add_cover(vp: VersionPlan, src_t: float, track: Track, workdir: Path) -> bool:
    ti = O.fit_hook(vp.hook.text, vp.look.font, vp.look.hook_style, start_size=96)
    text = vp.hook.text
    if ti is None:  # short form: first words that fit
        ws = vp.hook.text.split()
        while ws and ti is None:
            ws = ws[:-1]
            ti = O.fit_hook(" ".join(ws), vp.look.font, vp.look.hook_style, start_size=96) if ws else None
        text = " ".join(ws)
    if ti is None:
        return False
    geo = vp.geo
    png = O.save(ti, workdir / f"v{vp.idx}_cover_text.png")
    w, h = ti.image.size
    ot = max(0.0, geo.out_t(src_t))
    x, y = place(w, h, ot, ot, HOOK_SLOTS, track, geo)
    vp.cover_src_t = round(src_t, 3)
    vp.cover_text = text
    vp.cover_overlay = Overlay("cover", text, str(png), x, y, w, h, ot, ot, ti.cap_px)
    return True


# ---------------------------------------------------------------- posting order (R8)


def posting_order(plans: list[VersionPlan]) -> list[VersionPlan]:
    from .look import differences
    from .writing import key

    def unlike(a: VersionPlan, b: VersionPlan) -> int:
        return len(differences(a.look, b.look)) + (3 if a.hook.pattern != b.hook.pattern else 0)

    def opener(p: VersionPlan) -> str:
        return " ".join(key(p.hook.text).split()[:2])

    counts: dict[str, int] = {}
    for p in plans:
        counts[opener(p)] = counts.get(opener(p), 0) + 1
    unique = [p for p in plans if counts[opener(p)] == 1]
    shared = [p for p in plans if counts[opener(p)] > 1]
    order = [unique.pop(0)] if unique else [shared.pop(0)]
    while unique:
        nxt = max(unique, key=lambda p: unlike(p, order[-1]))
        unique.remove(nxt)
        order.append(nxt)
    # versions that open with the same words go last, as far apart as possible
    groups: dict[str, list[VersionPlan]] = {}
    for p in shared:
        groups.setdefault(opener(p), []).append(p)
    while any(groups.values()):
        for g in list(groups):
            if groups[g]:
                order.append(groups[g].pop(0))
    for i, p in enumerate(order, 1):
        p.post_order = i
    return order
