"""Rules every version must pass before the user sees it (R6, design 1.7). Empty list = pass."""
from __future__ import annotations

import itertools

from . import config as C
from . import media
from .face import Track
from .look import differences
from .plan import VersionPlan, face_boxes, in_safe_area, overlap
from .transcript import Transcript
from .writing import caption_problems, hook_problems, key


def plan_problems(vp: VersionPlan, t: Transcript, track: Track) -> list[str]:
    p = []
    geo = vp.geo
    hooks = [o for o in vp.overlays if o.kind == "hook"]
    if len(hooks) != 1:
        p.append("version must have exactly one hook")
    for o in vp.overlays + ([vp.cover_overlay] if vp.cover_overlay else []):
        name = f"{o.kind} {o.text!r}"
        if not in_safe_area(o.box):
            p.append(f"{name}: outside the safe area {o.box}")
        if o.cap_px < C.MIN_TEXT_PX:
            p.append(f"{name}: text {o.cap_px}px tall (min {C.MIN_TEXT_PX})")
        if o.kind == "cover":
            continue
        d = o.t1 - o.t0
        if d < C.MIN_ON_SCREEN_S - 1e-6:
            p.append(f"{name}: on screen {d:.2f}s (min {C.MIN_ON_SCREEN_S})")
        if o.kind == "hook" and not (C.HOOK_MIN_S - 1e-6 <= d <= C.HOOK_MAX_S + 1e-6):
            p.append(f"hook on screen {d:.2f}s (must be {C.HOOK_MIN_S}-{C.HOOK_MAX_S})")
        if o.kind != "hook" and d > C.LABEL_MAX_S + 1e-6:
            p.append(f"{name}: on screen {d:.2f}s (max {C.LABEL_MAX_S})")
        if o.t1 > vp.out_duration + 1e-3:
            p.append(f"{name}: shown after the video ends")
        # every face sample (10 fps) during the overlay's time on screen
        for fb in face_boxes(track, geo, o.t0, o.t1):
            if overlap(o.box, fb):
                p.append(f"{name}: covers the face")
                break
    if vp.cover_overlay:
        s = min(track.samples, key=lambda s: abs(s.t - vp.cover_src_t))
        if s.face and overlap(vp.cover_overlay.box, geo.out_box(s.face, C.FACE_PAD)):
            p.append("cover text covers the face")
    else:
        p.append("no cover")
    caps = [o for o in vp.overlays if o.kind == "caption"]
    if caps and hooks and min(c.t0 for c in caps) < hooks[0].t1 - 1e-6:
        p.append("captions overlap the hook")
    for a, b in zip(caps, caps[1:]):
        if b.t0 < a.t1 - 1e-6:
            p.append(f"captions {a.text!r} and {b.text!r} overlap in time")
    for c in caps:
        if not 1 <= len(c.text.split()) <= 4:
            p.append(f"caption {c.text!r} must be 1-4 words")
    # zoom must not crop the face or hands
    if vp.look.zoom > 1.0:
        for s in track.samples:
            for b in ([s.face] if s.face else []) + s.hands:
                if not geo.in_crop(b):
                    p.append(f"zoom crops the face or hands at {s.t:.1f}s")
                    break
            else:
                continue
            break
    # never cut into the first word
    if vp.look.trim > 0 and t.words and vp.look.trim > t.words[0].safe_start + 1e-6:
        p.append("start trim cuts into the first word")
    hp = hook_problems(vp.hook, t, own=vp.hook.pattern == "own")
    p += [f"hook: {x}" for x in hp]
    p += [f"caption: {x}" for x in caption_problems(vp.post_caption, t)]
    return p


def file_problems(vp: VersionPlan, path, src_dur: float) -> list[str]:
    """Checks on the rendered file itself."""
    p = []
    info = media.ffprobe(path)
    vs = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    aus = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    if len(vs) != 1 or vs[0].get("codec_name") != "h264" or (vs[0].get("width"), vs[0].get("height")) != (C.W, C.H):
        p.append(f"video must be one 1080x1920 H.264 stream, got {[(s.get('codec_name'), s.get('width'), s.get('height')) for s in vs]}")
    if len(aus) != 1:
        p.append(f"must have exactly one audio stream (the original voice), got {len(aus)}")
    dur = float((info.get("format") or {}).get("duration") or 0)
    expected = (src_dur - vp.look.trim) / vp.look.speed
    if abs(dur - expected) > 0.25 * expected:
        p.append(f"duration {dur:.2f}s, expected about {expected:.2f}s")
    if vp.look.trim > 0:
        # the cut at the start must land in quiet audio, not in a word
        head = media.frame_db(media.load_audio(path, 0.0, C.CUT_WINDOW_S))
        whole = media.frame_db(media.load_audio(path))
        if float(head.max()) > media.quiet_threshold(whole):
            p.append("voice is clipped at the start cut")
    return p


def set_problems(plans: list[VersionPlan]) -> list[str]:
    """Across all delivered versions together."""
    p = []
    hooks = [key(v.hook.text) for v in plans]
    if len(set(hooks)) != len(hooks):
        p.append("two versions have the same hook")
    caps = [key(v.post_caption) for v in plans]
    if len(set(caps)) != len(caps):
        p.append("two versions have the same caption")
    if len({v.look for v in plans}) != len(plans):
        p.append("two versions have the same look")
    for a, b in itertools.combinations(plans, 2):
        d = differences(a.look, b.look)
        if len(d) < C.MIN_LOOK_CHANGES:
            p.append(f"versions {a.idx} and {b.idx} differ in only {len(d)} settings ({', '.join(d)})")
    covers = [(v.cover_src_t, key(v.cover_text)) for v in plans]
    if len(set(covers)) != len(covers):
        p.append("two versions have the same cover")
    return p

