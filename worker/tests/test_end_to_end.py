"""R11 on the synthetic clip: 4 versions come back, each passes every check, files are right."""
import json

from trialreels import checks, media, pipeline


def test_full_run(clip, tmp_path):
    video, transcript = clip
    rep = pipeline.run(video, tmp_path / "out", n=4, transcript_path=transcript, offline=True, quiet=True)
    assert len(rep["versions"]) == 4, rep["dropped"]
    hooks = [v["hook"] for v in rep["versions"]]
    caps = [v["caption"] for v in rep["versions"]]
    assert len(set(hooks)) == 4 and len(set(caps)) == 4
    assert sorted(v["post_order"] for v in rep["versions"]) == [1, 2, 3, 4]
    for v in rep["versions"]:
        out = tmp_path / "out"
        info = media.ffprobe(out / v["video"])
        vs = [s for s in info["streams"] if s["codec_type"] == "video"][0]
        assert (vs["codec_name"], vs["width"], vs["height"]) == ("h264", 1080, 1920)
        assert v["what_changed"][0].startswith("hook: ")
        assert (out / v["cover"]).stat().st_size > 10_000
        from PIL import Image
        assert Image.open(out / v["cover"]).size == (1080, 1920)
        assert "\n" not in v["caption"].strip()
    page = (tmp_path / "out" / "README.md").read_text()
    assert "At most 5 trials a day" in page and "This run took" in page
    assert json.loads((tmp_path / "out" / "report.json").read_text())["cost"]["compute_s"] > 0


def test_own_hook_is_used(clip, tmp_path):
    video, transcript = clip
    rep = pipeline.run(video, tmp_path / "out", n=2, own_hook="My favourite money hack", transcript_path=transcript,
                       offline=True, quiet=True)
    assert "My favourite money hack" in [v["hook"] for v in rep["versions"]]
