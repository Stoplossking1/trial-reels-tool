"""The look of each version (R5): pick settings so every pair differs in at least 3 of them."""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, asdict

from . import config as C


@dataclass(frozen=True)
class Look:
    speed: float
    mirror: bool
    zoom: float
    brightness: float
    saturation: float
    font: str
    caption_size: str
    hook_style: str
    trim: float        # seconds cut off the start; never more than the quiet time before the first word
    crf: int
    gop: int

    def to_dict(self) -> dict:
        return asdict(self)


def differences(a: Look, b: Look) -> list[str]:
    """Settings on which a and b really differ (numbers must be at least MIN_DIFF apart)."""
    d = C.MIN_DIFF
    out = []
    if abs(a.speed - b.speed) >= d["speed"] - 1e-9:
        out.append("speed")
    if a.mirror != b.mirror:
        out.append("mirror")
    if abs(a.zoom - b.zoom) >= d["zoom"] - 1e-9:
        out.append("zoom")
    if abs(a.brightness - b.brightness) >= d["brightness"] - 1e-9 or \
            abs(a.saturation - b.saturation) >= d["saturation"] - 1e-9:
        out.append("colour")
    if a.font != b.font:
        out.append("caption font")
    if a.caption_size != b.caption_size:
        out.append("caption size")
    if a.hook_style != b.hook_style:
        out.append("hook style")
    if abs(a.trim - b.trim) >= d["trim"] - 1e-9:
        out.append("start trim")
    if abs(a.crf - b.crf) >= d["crf"] or a.gop != b.gop:
        out.append("re-export")
    return out


def all_pairs_ok(looks: list[Look]) -> bool:
    return all(len(differences(a, b)) >= C.MIN_LOOK_CHANGES for a, b in itertools.combinations(looks, 2))


def _r(rng: random.Random, lo: float, hi: float, step: float) -> float:
    k = int(round((hi - lo) / step))
    return round(lo + step * rng.randint(0, k), 3)


def random_look(rng: random.Random, fonts: list[str], allow_mirror: bool, crf: int, gop: int,
                max_trim: float = C.TRIM_RANGE[1], max_zoom: float = C.ZOOM_RANGE[1]) -> Look:
    lo, hi = C.TRIM_RANGE[0], min(C.TRIM_RANGE[1], max_trim)
    return Look(
        speed=_r(rng, *C.SPEED_RANGE, 0.01),
        mirror=allow_mirror and rng.random() < 0.5,
        zoom=_r(rng, C.ZOOM_RANGE[0], max(C.ZOOM_RANGE[0], min(C.ZOOM_RANGE[1], max_zoom)), 0.005),
        brightness=_r(rng, *C.BRIGHTNESS_RANGE, 0.005),
        saturation=_r(rng, *C.SATURATION_RANGE, 0.005),
        font=rng.choice(fonts),
        caption_size=rng.choice(list(C.CAPTION_SIZES)),
        hook_style=rng.choice(C.HOOK_STYLES),
        trim=_r(rng, lo, hi, 0.1) if hi >= lo else 0.0,
        crf=crf,
        gop=gop,
    )


def make_looks(n: int, seed: int, fonts: list[str], allow_mirror: bool = True,
               max_trim: float = C.TRIM_RANGE[1], max_zoom: float = C.ZOOM_RANGE[1], tries: int = 5000) -> list[Look]:
    """n looks, pairwise >= 3 real differences, no two identical. Re-export always differs."""
    rng = random.Random(seed)
    crfs = rng.sample(list(C.CRF_CHOICES), k=min(n, len(C.CRF_CHOICES)))
    while len(crfs) < n:
        crfs.append(rng.choice(C.CRF_CHOICES))
    gops = rng.sample(list(C.GOP_CHOICES), k=min(n, len(C.GOP_CHOICES)))
    while len(gops) < n:
        gops.append(rng.choice(C.GOP_CHOICES))
    for _ in range(tries):
        looks = [random_look(rng, fonts, allow_mirror, crfs[i], gops[i], max_trim, max_zoom) for i in range(n)]
        if all_pairs_ok(looks) and len(set(looks)) == n:
            return looks
    raise RuntimeError("could not find looks that differ enough")


def replacement(existing: list[Look], seed: int, fonts: list[str], allow_mirror: bool, crf: int, gop: int,
                max_trim: float = C.TRIM_RANGE[1], max_zoom: float = C.ZOOM_RANGE[1], tries: int = 5000) -> Look:
    """A new look for one version that failed its checks, still >= 3 different from all others."""
    rng = random.Random(seed)
    for _ in range(tries):
        lk = random_look(rng, fonts, allow_mirror, crf, gop, max_trim, max_zoom)
        if all(len(differences(lk, o)) >= C.MIN_LOOK_CHANGES for o in existing) and lk not in existing:
            return lk
    raise RuntimeError("could not find a replacement look")


def describe(lk: Look, captions_on: bool) -> list[str]:
    out = [f"{lk.speed:g}x"]
    out.append("mirrored" if lk.mirror else "not mirrored")
    if lk.zoom > 1.0:
        out.append(f"zoom {round((lk.zoom - 1) * 100, 1):g}%")
    out.append(f"colour +{lk.brightness:g} brightness, x{lk.saturation:g} saturation")
    if captions_on:
        out.append(f"{lk.font} {lk.caption_size} captions")
    out.append({"white_shadow": "white hook with shadow", "black_on_white_pill": "black hook on white pill",
                "white_on_black_pill": "white hook on black pill"}[lk.hook_style])
    if lk.trim > 0:
        out.append(f"starts {lk.trim:.1f}s later")
    out.append(f"export quality {lk.crf}")
    return out
