"""R5: every pair of versions differs in at least 3 settings, all within range."""
import itertools

from trialreels import config as C
from trialreels.look import differences, make_looks


def test_looks_differ_enough_and_stay_in_range():
    for seed in range(30):
        for n in (2, 4, 5):
            looks = make_looks(n, seed, ["Jost", "Inter", "SF Pro Display"], allow_mirror=True, max_trim=0.6)
            assert len(set(looks)) == n
            for a, b in itertools.combinations(looks, 2):
                assert len(differences(a, b)) >= 3
            for lk in looks:
                assert C.SPEED_RANGE[0] <= lk.speed <= C.SPEED_RANGE[1]
                assert C.ZOOM_RANGE[0] <= lk.zoom <= C.ZOOM_RANGE[1]
                assert lk.trim <= 0.6 and (lk.trim == 0 or lk.trim >= C.TRIM_RANGE[0])
                assert lk.font != "Avenir Next"


def test_no_mirror_when_video_has_text():
    looks = make_looks(5, 1, ["Jost", "Inter"], allow_mirror=False)
    assert not any(lk.mirror for lk in looks)


def test_no_trim_when_first_word_starts_immediately():
    looks = make_looks(4, 2, ["Jost", "Inter"], max_trim=0.1)
    assert all(lk.trim == 0 for lk in looks)
