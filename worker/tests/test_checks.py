"""R6 / design 1.7: the checks catch what they must, and a good plan passes."""
import dataclasses
import itertools

import pytest

from trialreels import checks, config as C, overlays
from trialreels.look import Look
from trialreels.plan import Overlay, add_cover, build, cover_times, posting_order
from trialreels.writing import Hook

FONTS = overlays.available_fonts()
LOOK = Look(1.2, False, 1.02, 0.01, 1.02, FONTS[0], "medium", "white_shadow", 0.3, 20, 60)


@pytest.fixture
def good(transcript, track, tmp_path):
    vp = build(1, Hook("3 apps I stopped paying for", "number_first"), LOOK, transcript, track, 16.5, tmp_path)
    assert vp
    vp.post_caption = "three apps i stopped paying for this year"
    assert add_cover(vp, cover_times(transcript, track, 1, 16)[0], track, tmp_path)
    return vp


def test_good_plan_passes(good, transcript, track):
    assert checks.plan_problems(good, transcript, track) == []


def test_hook_timing_and_captions(good):
    hook = good.overlays[0]
    assert hook.kind == "hook" and C.HOOK_MIN_S <= hook.t1 - hook.t0 <= C.HOOK_MAX_S
    caps = good.overlays[1:]
    assert caps and all(C.MIN_ON_SCREEN_S - 1e-6 <= c.t1 - c.t0 <= C.LABEL_MAX_S for c in caps)
    assert all(1 <= len(c.text.split()) <= 4 for c in caps)
    assert min(c.t0 for c in caps) >= hook.t1


def moved(vp, **kw):
    vp.overlays[0] = dataclasses.replace(vp.overlays[0], **kw)
    return vp


def test_outside_safe_area(good, transcript, track):
    assert any("safe area" in p for p in checks.plan_problems(moved(good, y=100), transcript, track))


def test_under_like_buttons(good, transcript, track):
    vp = moved(good, x=C.BUTTONS_X - 50, y=C.BUTTONS_Y + 20, w=120, h=100)
    assert any("safe area" in p for p in checks.plan_problems(vp, transcript, track))


def test_too_small(good, transcript, track):
    assert any("px tall" in p for p in checks.plan_problems(moved(good, cap_px=20), transcript, track))


def test_too_short_on_screen(good, transcript, track):
    assert any("on screen" in p for p in checks.plan_problems(moved(good, t1=1.0), transcript, track))


def test_hook_too_long_on_screen(good, transcript, track):
    assert any("hook on screen" in p for p in checks.plan_problems(moved(good, t1=3.4), transcript, track))


def test_text_on_face(good, transcript, track):
    s = next(s for s in track.samples if s.face)
    x0, y0, x1, y1 = good.geo.out_box(s.face)
    vp = moved(good, x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
    assert any("covers the face" in p for p in checks.plan_problems(vp, transcript, track))


def test_zoom_that_crops_face(good, transcript, track):
    vp = dataclasses.replace(good, look=dataclasses.replace(LOOK, zoom=8.0))
    assert any("zoom crops" in p for p in checks.plan_problems(vp, transcript, track))


def test_trim_into_first_word(good, transcript, track):
    vp = dataclasses.replace(good, look=dataclasses.replace(LOOK, trim=transcript.words[0].start + 0.1))
    assert any("first word" in p for p in checks.plan_problems(vp, transcript, track))


def test_bad_caption(good, transcript, track):
    good.post_caption = "Three Apps #saas"
    assert any(p.startswith("caption:") for p in checks.plan_problems(good, transcript, track))


def test_set_rules(good):
    twin = dataclasses.replace(good, idx=2)
    probs = checks.set_problems([good, twin])
    assert any("same hook" in p for p in probs) and any("same caption" in p for p in probs)
    assert any("differ in only" in p for p in probs)


def test_cover_frames_are_between_words_and_apart(transcript, track):
    from trialreels.transcript import in_word
    ts = cover_times(transcript, track, 4, 16)
    assert len(ts) == 4
    assert all(not in_word(transcript, t) for t in ts)
    assert all(abs(a - b) >= 1.0 for a, b in itertools.combinations(ts, 2))


def test_posting_order_puts_same_openers_last(good):
    a = dataclasses.replace(good, idx=1, hook=Hook("Stop paying for Canva", "problem_first"))
    b = dataclasses.replace(good, idx=2, hook=Hook("Stop paying for apps", "problem_first"))
    c = dataclasses.replace(good, idx=3, hook=Hook("3 apps I cancelled", "number_first"),
                            look=dataclasses.replace(LOOK, mirror=True, speed=1.15))
    order = posting_order([a, b, c])
    assert order[0].idx == 3 and {p.idx for p in order[1:]} == {1, 2}
