# trialreels: the video worker (milestone M1)

One vertical talking-head video in, up to 5 trial-reel versions out: each with its own hook, look, cover and
caption, checked against every rule in `docs/ready.md` before it is delivered. Design: `docs/plans/2026-10-03-trial-reels-design.md`.

## Setup

```bash
sudo apt-get install ffmpeg libegl1 libgles2      # macOS: brew install ffmpeg
cd worker && pip install -e ".[dev]"
```

Put the licensed fonts in `worker/fonts/` (see `fonts/README.md`). Jost and Inter are already there.

Keys (environment variables):

| Variable | Used for |
|---|---|
| `DEEPGRAM_API_KEY` | the transcript (word times) |
| `ANTHROPIC_API_KEY` | writing hooks and captions with Claude |

## Use

```bash
# 1. transcript, then fix misheard words in the JSON "text" fields (keep the times)
trialreels transcribe fixtures/raw/IMG_4239.MOV --out out/day1/transcript.json

# 2. make 4 versions
trialreels run fixtures/raw/IMG_4239.MOV --out out/day1 --transcript out/day1/transcript.json

# options: --versions 1-5   --hook "your own hook"   --has-text (never mirror)   --no-captions
#          --offline (no Claude: hooks are sentences cut from the transcript)
```

`out/day1/` then holds `01_<pattern>.mp4`, `01_<pattern>_cover.jpg`, `01_<pattern>_caption.txt`, ... in posting
order, `README.md` (the download page: posting guide, what changed, run time), `report.json` (everything, incl.
cost and per-step timing) and `_work/` (plans, overlay images, face track).

Bad inputs exit with code 2 and the plain message, e.g. `REJECTED (sideways): This video is sideways. Upload a vertical one.`

## Tests

```bash
cd worker && python -m pytest -q
```

They build a synthetic talking head (public-domain NASA portrait + tone bursts as words), so they need no keys
and no real video. When `fixtures/raw/` has the real test videos, run them through by hand (see above).

## How a run works

`validate → transcribe → face track → write hooks/captions → pick looks → plan → check plan → render → check file → order`

- `media.py`: input rules (R2), audio loading.
- `transcript.py`: Deepgram word times, then safe cut points measured from the audio itself.
- `face.py`: MediaPipe face/mouth/eyes/hands at 10 fps; looks at square sections of the tall frame so smaller
  faces are still found.
- `writing.py`: hooks (R4) and captions (R7). Claude writes, code rejects anything with a number or name that
  isn't said in the video, too long, duplicated, or breaking the caption rules.
- `look.py`: speed, mirror, zoom, colour, font, caption size, hook style, trim, export (R5); every pair of
  versions differs in at least 3.
- `plan.py`: where text goes (never on the face, always in the safe area), caption timing, cover frames,
  posting order (R8).
- `render.py`: FFmpeg. Mirror before text, pitch kept on speed-up, HDR phone video tone-mapped, no music.
- `checks.py`: every R6 rule, per version and across versions. A failing version is re-planned (up to 2 times)
  or dropped.
