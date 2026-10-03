"""R2 / R11: bad inputs get a clear message (and the pipeline never reaches anything billable)."""
import subprocess

import pytest

import fixture
from trialreels import media
from trialreels.errors import InputRejected


def reason(path):
    with pytest.raises(InputRejected) as e:
        media.validate(path)
    return e.value


def test_sideways(tmp_path):
    v, _ = fixture.make(tmp_path, landscape=True, seconds=8)
    e = reason(v)
    assert e.code == "sideways" and e.message == "This video is sideways. Upload a vertical one."


def test_too_long(tmp_path):
    v, _ = fixture.make(tmp_path, seconds=180)
    assert reason(v).code == "too_long"


def test_too_short(tmp_path):
    v, _ = fixture.make(tmp_path, seconds=3)
    assert reason(v).code == "too_short"


def test_no_audio_track(tmp_path):
    out = tmp_path / "noaudio.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=1080x1920:d=8",
                    "-c:v", "libx264", "-preset", "ultrafast", str(out)], check=True)
    assert reason(out).code == "silent"


def test_silent_audio_is_rejected_before_transcription(tmp_path):
    from trialreels.transcript import transcribe
    v, _ = fixture.make(tmp_path, silent=True, seconds=8)
    media.validate(v)  # has an audio track ...
    with pytest.raises(InputRejected) as e:
        transcribe(v, tmp_path)  # ... but nothing on it: rejected before any API call
    assert e.value.code == "silent"


def test_not_a_video(tmp_path):
    f = tmp_path / "x.mp4"
    f.write_text("hello")
    assert reason(f).code == "bad_format"


def test_not_9_16(tmp_path):
    out = tmp_path / "square.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=1080x1350:d=8",
                    "-f", "lavfi", "-i", "sine=d=8", "-c:v", "libx264", "-preset", "ultrafast", "-shortest",
                    str(out)], check=True)
    assert reason(out).code == "not_9_16"


def test_rotation_tag_portrait_is_vertical(tmp_path):
    """Phones store portrait as landscape + a rotation tag. That is vertical, not sideways."""
    src = tmp_path / "land.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=1920x1080:d=8",
                    "-f", "lavfi", "-i", "sine=d=8", "-c:v", "libx264", "-preset", "ultrafast", "-shortest",
                    str(src)], check=True)
    rot = tmp_path / "rot.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-display_rotation", "90", "-i", str(src), "-c", "copy", str(rot)],
                   check=True)
    info = media.validate(rot)
    assert (info.width, info.height) == (1080, 1920)
