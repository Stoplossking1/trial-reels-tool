"""trialreels run INPUT --out DIR   (see README.md)"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config as C
from .errors import InputRejected, RunFailed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="trialreels", description="One vertical video in, trial-reel versions out.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="make the versions")
    r.add_argument("input")
    r.add_argument("--out", required=True)
    r.add_argument("--versions", type=int, default=C.DEFAULT_VERSIONS, help="1-5, default 4")
    r.add_argument("--hook", help="your own hook text (used as one version)")
    r.add_argument("--has-text", action="store_true", help="the video has filmed text: never mirror")
    r.add_argument("--no-captions", action="store_true", help="don't burn word captions into the video")
    r.add_argument("--transcript", help="transcript JSON (e.g. from `transcribe`, after fixing words)")
    r.add_argument("--track", help="face track JSON from an earlier run (_work/track.json)")
    r.add_argument("--offline", action="store_true", help="no Claude: hooks and captions cut from the transcript")
    r.add_argument("--seed", type=int)

    t = sub.add_parser("transcribe", help="transcript only, to fix misheard words before `run`")
    t.add_argument("input")
    t.add_argument("--out", required=True, help="transcript JSON path")

    v = sub.add_parser("validate", help="only check the input")
    v.add_argument("input")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "validate":
            from .media import validate
            print(json.dumps(validate(a.input).to_dict(), indent=1))
        elif a.cmd == "transcribe":
            from .media import validate
            from .transcript import transcribe
            validate(a.input)
            out = Path(a.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            transcribe(a.input, out.parent).save(out)
            print(f"wrote {out}. Fix misheard words in the \"text\" fields (keep the times), then pass --transcript.")
        else:
            from .pipeline import run
            rep = run(a.input, a.out, a.versions, a.hook, a.has_text, a.transcript, a.track, a.offline, a.seed,
                      not a.no_captions)
            print(f"\n{len(rep['versions'])} versions in {rep['seconds']}s -> {a.out}")
            for v in rep["versions"]:
                print(f"  {v['post_order']}. {v['hook']!r}  [{'; '.join(v['what_changed'])}]")
            for d in rep["dropped"]:
                print(f"  dropped version {d['version']}: {'; '.join(d['why'][:3])}")
    except InputRejected as e:
        print(f"REJECTED ({e.code}): {e.message}", file=sys.stderr)
        return 2
    except RunFailed as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
