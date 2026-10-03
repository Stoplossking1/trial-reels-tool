"""One run, end to end (design 1): validate, transcribe, plan, render, check, deliver."""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import checks, config as C, face, look as L, media, overlays, plan as P, render, writing
from .errors import RunFailed
from .transcript import Transcript, finish, transcribe

RENDER_WORKERS = 2

PATTERN_NAMES = {"number_first": "number first", "problem_first": "threat or problem first", "how_to": "how to",
                 "named_thing": "named person or thing", "question": "question", "own": "your own hook"}

POSTING_GUIDE = """## How to post these

1. Post every version as a trial reel. "Trial" on. "Share automatically with everyone" **off**.
2. **At most 5 trials a day.** Guides report a cap of about 5; going over can block trials for 30 days.
3. Post order: the version least like the last one goes next. Versions that open with the same words go last
   and far apart. (The numbers below are already in this order.)
4. Set each version's cover and paste its own caption.
5. After 24 hours, compare views. Share the top one to your profile only if it has about **double** the middle one.
   If they are close, share your original. A few hundred views apart is noise, not a winner.
"""


class Log:
    def __init__(self, quiet: bool = False):
        self.t0 = time.time()
        self.quiet = quiet
        self.steps: dict[str, float] = {}
        self._last = self.t0

    def step(self, name: str) -> None:
        now = time.time()
        self.steps[name] = round(now - self._last, 2)
        self._last = now
        if not self.quiet:
            print(f"[{now - self.t0:6.1f}s] {name}", flush=True)

    @property
    def total(self) -> float:
        return round(time.time() - self.t0, 1)


def _seed(path: Path) -> int:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read(1 << 20))
    return int(h.hexdigest()[:8], 16)


def get_hooks(t: Transcript, n: int, own_hook: str | None, use_claude: bool, usage: writing.Usage):
    wanted = n + 3  # spares, for hooks that don't fit on screen in a given font
    cands = writing.claude_hooks(t, wanted + 3, usage) if use_claude else writing.offline_hooks(t)
    hooks, notes = writing.pick_hooks(cands, wanted, t, own_hook)
    if use_claude and len(hooks) < n:
        more = writing.claude_hooks(t, wanted, usage, avoid=[h.text for h in hooks])
        hooks, notes2 = writing.pick_hooks(cands + more, wanted, t, own_hook)
        notes += notes2
    return hooks, notes


def run(src: str | Path, out_dir: str | Path, n: int = C.DEFAULT_VERSIONS, own_hook: str | None = None,
        has_text: bool = False, transcript_path: str | Path | None = None, track_path: str | Path | None = None,
        offline: bool = False, seed: int | None = None, captions_on: bool = True, quiet: bool = False,
        hooks_file: str | Path | None = None, captions_file: str | Path | None = None) -> dict:
    """hooks_file / captions_file: hand-written candidates (JSON). They pass the same checks as Claude's."""
    src, out = Path(src), Path(out_dir)
    n = max(1, min(int(n), C.MAX_VERSIONS))
    out.mkdir(parents=True, exist_ok=True)
    work = out / "_work"
    work.mkdir(exist_ok=True)
    log = Log(quiet)

    info = media.validate(src)
    log.step("validated")

    if transcript_path:
        t = finish(Transcript.load(transcript_path), src)
    else:
        t = transcribe(src, work)
    t.save(out / "transcript.json")
    log.step(f"transcript ({len(t.words)} words, {len(t.sentences)} sentences)")

    track = face.Track.load(track_path) if track_path else face.track(src)
    track.save(work / "track.json")
    faces_seen = sum(1 for s in track.samples if s.face) / max(1, len(track.samples))
    log.step(f"face tracking ({faces_seen:.0%} of frames have a face)")

    use_claude = not offline and writing.have_claude()
    if not offline and not use_claude:
        raise RunFailed("No Claude credentials (ANTHROPIC_API_KEY). Set them, or pass --offline for transcript-cut hooks.")
    usage = writing.Usage()
    if hooks_file:
        cands = [writing.Hook(h["text"], h["pattern"], h.get("source_quote", "")) for h in json.loads(Path(hooks_file).read_text())]
        hooks, hook_notes = writing.pick_hooks(cands, n + 3, t, own_hook)
    else:
        hooks, hook_notes = get_hooks(t, n, own_hook, use_claude, usage)
    if not hooks:
        raise RunFailed("No hook passed the checks. " + " | ".join(hook_notes[:5]))
    log.step(f"hooks ({len(hooks)} usable, {len(hook_notes)} rejected)")

    fonts = overlays.available_fonts()
    if not fonts:
        raise RunFailed(f"No caption fonts found in {C.FONT_DIR}")
    seed = _seed(src) if seed is None else seed
    max_trim = max(0.0, t.words[0].safe_start - 0.05)
    n_plan = min(n, len(hooks))
    max_zoom = P.max_safe_zoom(track)
    looks = L.make_looks(n_plan, seed, fonts, allow_mirror=not has_text, max_trim=max_trim, max_zoom=max_zoom)

    if captions_file:
        cap_cands = json.loads(Path(captions_file).read_text())
    elif use_claude:
        cap_cands = writing.claude_captions(t, [h.text for h in hooks[:n_plan]], usage)
    else:
        cap_cands = writing.offline_captions(t, n_plan)
    post_caps = writing.pick_captions(cap_cands, n_plan, t)
    cover_ts = P.cover_times(t, track, n_plan * 2, info.duration - 0.5)
    log.step(f"writing done ({len(post_caps)} captions, {len(cover_ts)} cover frames)")

    plans: list[P.VersionPlan] = []
    rejected: list[dict] = []
    spare_hooks = list(hooks)
    for i in range(n_plan):
        if i >= len(post_caps) or not spare_hooks:
            rejected.append({"version": i + 1, "why": ["ran out of distinct captions or hooks"]})
            continue
        lk = looks[i]
        vp, why = None, []
        for attempt in range(3):  # first look, then up to 2 re-plans (design 1.7)
            for h in list(spare_hooks):
                vp = P.build(i + 1, h, lk, t, track, info.duration, work, captions_on)
                if vp:
                    break
            if vp is None:
                why = ["no remaining hook fits on screen"]
                break
            vp.post_caption = post_caps[i]
            cover_t = next((c for c in cover_ts if all(abs(c - p.cover_src_t) >= 1.0 for p in plans)), None)
            if cover_t is None or not P.add_cover(vp, cover_t, track, work):
                why = ["no usable cover frame (mouth closed, eyes open, between words)"]
                vp = None
                break
            why = checks.plan_problems(vp, t, track)
            if not why:
                break
            vp = None
            if attempt < 2:
                others = [p.look for p in plans] + [l for j, l in enumerate(looks) if j > i]
                lk = L.replacement(others, seed + 101 * (attempt + 1) + i, fonts, not has_text, lk.crf, lk.gop,
                                   max_trim=max_trim, max_zoom=max_zoom)
        if vp is None:
            rejected.append({"version": i + 1, "why": why})
            continue
        spare_hooks.remove(vp.hook)
        vp.what_changed = [f"hook: {PATTERN_NAMES.get(vp.hook.pattern, vp.hook.pattern)}"] + L.describe(vp.look, captions_on)
        plans.append(vp)
    log.step(f"planned {len(plans)} versions ({len(rejected)} dropped)")

    def make(vp: P.VersionPlan):
        video = work / f"v{vp.idx}.mp4"
        cover = work / f"v{vp.idx}_cover.jpg"
        render.render(vp, str(src), video, info.hdr)
        render.cover(vp, str(src), cover, info.hdr)
        return vp, video, cover, checks.file_problems(vp, video, info.duration)

    delivered: list[P.VersionPlan] = []
    files: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=RENDER_WORKERS) as pool:  # each ffmpeg is itself multi-threaded
        for vp, video, cover, why in pool.map(make, plans):
            if why:
                rejected.append({"version": vp.idx, "why": why})
                continue
            delivered.append(vp)
            files[vp.idx] = {"video": video, "cover": cover}
            log.step(f"rendered version {vp.idx}")

    set_why = checks.set_problems(delivered)
    if set_why:
        raise RunFailed("versions are not different enough: " + "; ".join(set_why))
    if not delivered:
        raise RunFailed("no version passed the checks: " + json.dumps(rejected))

    ordered = P.posting_order(delivered)
    versions = []
    for vp in ordered:
        stem = f"{vp.post_order:02d}_{vp.hook.pattern}"
        v_out = out / f"{stem}.mp4"
        c_out = out / f"{stem}_cover.jpg"
        shutil.move(files[vp.idx]["video"], v_out)
        shutil.move(files[vp.idx]["cover"], c_out)
        (out / f"{stem}_caption.txt").write_text(vp.post_caption + "\n")
        versions.append({
            "post_order": vp.post_order, "video": v_out.name, "cover": c_out.name,
            "hook": vp.hook.text, "pattern": vp.hook.pattern, "caption": vp.post_caption,
            "what_changed": vp.what_changed, "duration_s": vp.out_duration, "plan": vp.to_dict(),
        })
    log.step("delivered")

    out_mb = sum(f.stat().st_size for f in out.iterdir() if f.is_file()) / 1e6
    report = {
        "input": info.to_dict(),
        "versions": versions,
        "dropped": rejected,
        "hook_rejections": hook_notes,
        "writer": "claude:" + C.CLAUDE_MODEL if use_claude else "offline (transcript cuts)",
        "seconds": log.total,
        "steps_s": log.steps,
        "cost": {
            "transcript_usd": t.cost_usd,
            "llm_usd": usage.usd,
            "llm_tokens": {"input": usage.input_tokens, "output": usage.output_tokens},
            "compute_s": log.total,
            "output_mb": round(out_mb, 1),
        },
    }
    (out / "report.json").write_text(json.dumps(report, indent=1, default=str))
    (out / "README.md").write_text(download_page(report))
    return report


def download_page(r: dict) -> str:
    lines = [f"# Your trial reels\n\nThis run took {r['seconds'] / 60:.1f} minutes.\n", POSTING_GUIDE,
             "## Versions, in posting order\n"]
    for v in r["versions"]:
        lines.append(f"### {v['post_order']}. \"{v['hook']}\"\n")
        lines.append(f"- Video: `{v['video']}`  \n- Cover: `{v['cover']}`  \n- Caption: {v['caption']}")
        lines.append("- What changed: " + "; ".join(v["what_changed"]) + "\n")
    if r["dropped"]:
        lines.append(f"\n{len(r['dropped'])} version(s) didn't pass the checks and were left out.")
    return "\n".join(lines) + "\n"
