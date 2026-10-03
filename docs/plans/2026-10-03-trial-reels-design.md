# Trial reel tool: build spec

Written 2026-10-03 from "Trial reel tool: what 'ready' means" (the product doc, saved as
`docs/ready.md`). That doc says **what** the tool must do. This one says **how** we build it, in what order, and how
each "must" gets checked. Section numbers like (R4) point to the product doc.

## 0. Decisions made here (change them before we start, not after)

| Decision | Choice | Why |
|---|---|---|
| Web app | Next.js (TypeScript) on Railway | Upload page, transcript editor, download page, admin. |
| Video worker | Python 3.12 + FFmpeg, one job per run, on Railway | All the real work is FFmpeg plus small checks. Python has the face and audio libraries. |
| Database | Railway Postgres | Decided 2026-10-03: Railway for hosting and database, no Supabase. |
| Files | Railway Storage Bucket (S3-compatible), presigned upload/download URLs | Same provider as the rest. |
| Sign-in | Clerk, Google only (changed 2026-10-03; see `2026-10-03-web-app-design.md`) | Sign-in is needed for the free run (R10). |
| Job queue | A `runs` table polled by the worker (`SELECT ... FOR UPDATE SKIP LOCKED`) | No extra service. Enough for launch volume. |
| Transcript | Paid speech-to-text API with **word timestamps** (Deepgram or OpenAI Whisper API); self-hosted Whisper revisited after M5 cost numbers | Word times drive hook timing, captions, trims and cut safety. |
| Hook and caption writing | Claude API, JSON output, then our own checks | The model writes; code decides if it is allowed (R4). |
| Face / mouth / eyes | MediaPipe Face Landmarker | Face box for "text never covers face", mouth and eye openness for the cover. |
| Payments | Stripe Checkout, credit packs (1 credit = 1 generation); see `2026-10-03-web-app-design.md` | R10. |
| Fonts | Instagram Sans (Jordan's copy), Jost (Futura look-alike), Inter (SF Pro look-alike) | Futura, SF Pro and Helvetica Neue files weren't available, and we don't use unlicensed copies. Jost and Inter are SIL Open Font License, committed in `worker/fonts/`. Instagram Sans, SF Pro Display and Helvetica Neue (Jordan's licensed copies) stay out of git and come from the private bucket. Jordan confirmed 2026-10-03 that his SF Pro and Helvetica Neue licences cover this use. |

## 1. The run, end to end

```
upload ─► validate ─► transcribe ─► user fixes transcript ─► plan versions ─► render ─► check ─► deliver
            │                                                     │              │         │
            └─ reject, no charge                                  │              │         └─ fail: re-plan that version (max 2), else drop it
                                                                  └─ hooks, captions, look, cover frame, posting order
```

States of a run (`runs.status`): `uploaded → validating → transcribing → awaiting_transcript → planning → rendering →
checking → done`, or `rejected` (input problem) or `failed` (our problem). Only `done` uses up the free run or a
payment (R10).

### 1.1 Upload (R2)

- Browser uploads straight to the Railway bucket with a presigned URL (no 500 MB through our server). Limit 500 MB enforced
  on the signed URL and again in the worker.
- Form fields: optional own hook (text), "my video has text in it, don't mirror" tickbox (the R2 "should", cheap to do
  now), number of versions (default 4, max 5).

### 1.2 Validate (R2, R11 error cases)

`ffprobe` the file. Reject with these exact messages:

| Check | Message |
|---|---|
| Not MOV/MP4 (by container, not file name) | "This file isn't a video we can read. Upload an MOV or MP4." |
| Width ≥ height after applying the rotation tag | "This video is sideways. Upload a vertical one." |
| Aspect not within 2% of 9:16 | "This video isn't 9:16. Upload a full-screen vertical video." |
| Under 5 s (no maximum length since 2026-10-03) | "This video is too short. Use at least 5 seconds." |
| No audio track, or speech under 2 s total after transcription | "We can't hear anyone talking in this video. The tool needs a spoken video." |
| Over 500 MB | "This video is over 500 MB." |

Note: phone videos often store portrait as landscape + a rotation tag. Read the tag (`side_data` rotation /
`displaymatrix`) before judging "sideways".

### 1.3 Transcribe

- Whisper with word timestamps. Then measure speech edges from the audio itself (energy, 10 ms frames) because Whisper
  word boundaries can be ±150 ms off. Store per word: `text, start, end, safe_start, safe_end`, where safe bounds are
  pushed outward to the nearest quiet point (below −40 dBFS for ≥ 60 ms).
- Sentences: split on Whisper punctuation; each sentence has a start/end from its words.

### 1.4 Transcript screen (R6 captions)

The user sees the transcript as editable words. They fix misheard words (text only, times stay). They press
"Make my versions". The fixed text is what hooks, captions and cover text are built from.

### 1.5 Plan the versions

The planner produces one JSON plan per version. Rendering never makes choices; it only follows the plan. This makes
every check below possible on the plan before we spend render time.

```jsonc
{
  "version": 2,
  "hook": { "text": "3 tools I stopped paying for", "pattern": "number_first", "source_words": [41, 48] },
  "speed": 1.2, "mirror": true, "zoom": 1.03,
  "color": { "brightness": 0.02, "saturation": 1.03 },
  "caption": { "on": true, "font": "Jost", "size": "medium" },
  "hook_style": "white_shadow",
  "start_trim_s": 0.5,
  "crf": 20,
  "cover": { "time_s": 6.4, "text": "3 tools I stopped paying for" },
  "post_caption": "the three apps i cancelled this month and what replaced them",
  "what_changed": ["hook: number first", "mirrored", "1.2x", "Jost captions", "zoom 3%"]
}
```

**Hooks (R4).** One Claude call with the fixed transcript and the pattern list from
`reference/research/hook-bank.md`. Ask for 8 candidates, each with its pattern and the word indexes it is based on.
Then code keeps only those that pass:
- under 10 words; fits in two lines at the chosen size inside the safe width (measured with the real font);
- every number and every capitalised name in the hook appears in the transcript (string match after normalising
  "three"/"3"); otherwise dropped;
- not the same text as another kept hook (case and punctuation ignored), and a different pattern from the others
  when there are enough patterns.
If the user typed a hook, it is version 1 and still goes through the length and fit checks (but not the "from the
video" check — it's their own words). If fewer good hooks than versions remain, ask once more; if still short, deliver
fewer versions and say why. Never pad with a duplicate hook.

**Look (R5).** Pick values from the R5 ranges. Generate combinations, then accept a set only when **every pair** of
versions differs in at least 3 of: speed, mirror, zoom, colour, caption font (Instagram Sans / SF Pro Display / Helvetica Neue / Jost / Inter), caption size, hook style, start trim,
re-export quality. "Differs" uses minimum steps so it's real: speed ≥ 0.04x apart, zoom ≥ 0.015 apart, brightness or
saturation ≥ 0.01 apart, trim ≥ 0.2 s apart, CRF ≥ 2 apart. Mirror is never used if the user ticked "has text".
Re-export always differs (CRF 18–24, plus a different GOP size) so every file is byte-different.

**Start trim.** Trim = min(chosen value, `safe_start` of the first word − 0.05 s). If the first word starts before
0.25 s, trim is 0 and doesn't count as a change.

**Hook timing (R6).** Hook appears at 0 and goes at the end of the first sentence (in output time, after trim and speed),
clamped to 1.5–3.0 s. If the first sentence is longer than 3 s, the hook still goes at 3.0 s.

**Captions (R6).** 1–4 words per group from the fixed transcript, breaking at punctuation and pauses > 250 ms. Each
group stays at least 1.2 s on screen (merge short groups; if still short, extend into the gap). Captions start after the
hook goes, so the two never overlap.

**Cover (R7).** Sample one frame every 0.1 s. Score = mouth closed (lip gap / face height under a threshold) AND eyes
open (eye aspect ratio above a threshold) AND not inside a word (between `safe_end` of one word and `safe_start` of the
next, or in a pause) AND low motion blur (variance of Laplacian). Pick the top-scoring frames that are ≥ 1 s apart, one
per version. Cover text = the hook, or a shortened hook if it doesn't fit at cover size.

**Post caption (R7).** One Claude call per run asking for N distinct captions, then code enforces: lower case, one line,
no `#`, at most one emoji, no `—` or `–`, ≤ 150 characters, no number or name not in the transcript, no two the same.
Optional comment-keyword line is a "should" (off at launch).

**Posting order (R8).** Order versions so each next one is the one least like the previous (count of differing
settings, hook pattern weighted ×3). Versions whose hooks share the same first two words go last and as far apart as
possible.

### 1.6 Render

One FFmpeg command per version, in this filter order (order matters):

1. `trim` start → 2. `hflip` if mirror → 3. scale/crop for zoom (centred on the face box, see 3.2) and scale to
1080x1920 → 4. `eq` brightness/saturation → 5. `setpts` + `atempo` for speed (keeps pitch) →
6. overlays: hook, captions (drawn **after** the mirror so our text is never backwards) → 7. encode H.264 High,
yuv420p, 30 fps, AAC 48 kHz, `-movflags +faststart`, chosen CRF and GOP.

Overlays are drawn as PNGs we render ourselves (Pillow with the real font files: shadow, pill, dark edge) and placed
with `overlay=enable='between(t,a,b)'`. That way we know every text box's exact pixels and times, which is what the
checks use. No music track is ever added (R5).

Cover: grab the chosen frame from the **rendered** version (so mirror/zoom/colour match), draw the cover text, save
1080x1920 JPG.

### 1.7 Check (R6, R11) — a version that fails is re-planned, never shown

All checks run on the plan **and** on the rendered output, across the whole video:

| Rule | How it's checked |
|---|---|
| Safe area: inside x 75–1005, y 270–1540 | Every overlay box from the render list, over its whole time span. |
| Nothing right of x 900 below y 1230 | Same. |
| Text ≥ 28 px tall | Cap height of each overlay's font size, measured from the rendered PNG. |
| On screen ≥ 1.2 s | Every overlay's `b − a`. |
| Hook 1.5–3.0 s, labels 1.5–3.5 s | Same. |
| Text never covers the face | Face box from MediaPipe on the **rendered video without overlays** at 10 fps (every frame within 100 ms); any overlap of a text box with the face box (padded 4%) in its time span = fail. Text moves to the other band (upper ↔ lower safe band) and the check reruns. |
| Zoom never crops face or hands | Face box (and hand boxes, MediaPipe Hands) of the source at 10 fps must stay inside the zoomed crop. Otherwise lower the zoom. |
| Output format | `ffprobe`: 1080x1920, h264, duration within ±25% of original ÷ speed. |
| No clipped words | For each cut (start and end), the audio within 40 ms of the cut is below −40 dBFS. End of file is never inside a word's `safe_end`. |
| No music added | Output has exactly one audio stream, from the source. |
| Hooks and captions unique, combos differ ≥ 3 | Checked on the plans of all delivered versions together. |

"Listen to each version start to finish" in R11 stays a human step for launch sign-off; the audio check above catches
it automatically in normal runs.

### 1.8 Deliver

Download page per run: for each version in posting order — video player, cover, caption with a copy button,
"what changed" list, download buttons; a "download all (zip)" button; and the posting guide from R8, word for word.
Shows "this run took N minutes". Files kept 14 days, then videos and covers are deleted; plans and costs are kept (daily cleanup job).

## 2. Data model (Postgres)

```
users          id, email, created_at, free_run_used_at (null until a run reaches done)
runs           id, user_id, status, error_code, error_message, input_path, input_meta jsonb,
               own_hook, has_text, n_versions, transcript jsonb, transcript_fixed jsonb,
               paid_via ('free' | 'stripe' | null), stripe_session_id,
               cost jsonb {transcribe, llm, compute_s, storage_mb, total_usd},
               started_at, finished_at
versions       id, run_id, idx, post_order, plan jsonb, video_path, cover_path, checks jsonb, status
```

Free run (R10): a run may start free only if `free_run_used_at` is null **and** no other free run of that user is in
progress. Set `free_run_used_at` only when the run reaches `done`. Rejected/failed runs leave it null and refund a paid
run through Stripe automatically. One account per verified email; Google sign-in counts as verified.

## 3. Money (R10)

- Every run records its real cost: transcription seconds × price, Claude input/output tokens × price, worker CPU/GPU
  seconds × price, storage MB × days × price. Shown per run and as averages in `/admin` next to the current price.
- Price is set after measuring 20 real runs (milestone M5). Starting guess for the page copy only: cost × 4.
- Charging: Stripe Checkout before the run starts; if the run ends `rejected` or `failed`, refund automatically.
  (Simpler than holding a card authorisation; can switch later.)

## 4. Build order

Each milestone ends with something we can run on `raw/IMG_4239.MOV` and `raw/E51D108D-...MOV`.

| # | Milestone | Done when |
|---|---|---|
| M1 | **Worker CLI, no web.** `trialreels run input.mov --versions 4 --out dir/` does validate → transcribe → plan → render → check, writes videos, covers, captions, `what_changed`, `report.json`. | Both test videos give 4 versions that pass every check in 1.7. |
| M2 | **Checks hardened.** Unit tests for each rule with made-up plans that should fail; golden test on both test videos. Validation tests with a sideways, 3-minute and silent clip. | All tests pass in CI. |
| M3 | **Web app.** Sign-in, upload, transcript fix screen, progress, download page with posting guide, run history. Worker pulls jobs from `runs` in Railway Postgres. | Jordan does a full run in the browser. |
| M4 | **Money.** Free run rule, Stripe Checkout, auto-refund on fail, cost tracking, `/admin`. | Free once, then pay; a failed run refunds and keeps the free run. |
| M5 | **Measure and launch.** 20 timed runs; set price; put run time on the page; R11 checklist signed off by a person. | Every R11 box ticked. |
| M6 | **Next version (shoulds).** First words heard change (move a stronger sentence to the start at clean cut points), comment-keyword line, per-change "may change" ticks. | After Jordan's 24-hour real test (R11 "after launch"). |

## 5. Repo layout

```
docs/            ready.md (product doc), plans/ (this design + implementation plans)
worker/          python package: validate.py transcribe.py plan/ (hooks.py look.py captions.py cover.py order.py)
                 render.py overlays.py checks/ (safe_area.py timing.py face.py audio.py uniqueness.py) cli.py
worker/tests/    unit + golden tests, fixtures (short clips, made-up plans)
worker/fonts/    Jost + Inter (OFL, committed); Instagram Sans downloaded from the bucket at start
web/             Next.js app
web/db/          migrations (Drizzle)
reference/research/hook-bank.md   copied from the content repo
```

## 6. Status

- **M1 built (2026-10-03)**, code in `worker/` (see `worker/README.md`). Runs end to end on a synthetic talking head;
  37 tests cover the input rules, writing rules, look rules, every R6 check and a full run.
  Not yet run on a real video (the day 1/day 2 files couldn't be downloaded into the build machine) or with real
  Deepgram/Claude keys (those calls are tested with faked responses).
- Changes from the plan above, found while building: the face detector looks at square sections of the tall frame
  (a whole 9:16 frame shrinks the face too much to find); faces and hands are tracked per frame without video-mode
  tracking; renders run two at a time.

## 7. Answers (2026-10-03)

1. Fonts: caption fonts are Instagram Sans, Jost and Inter (replacing Futura, SF Pro Display, Helvetica Neue in R5). Never Avenir Next still holds.
2. Test files: go in `fixtures/raw/` (videos, not in git, see `fixtures/README.md`), `reference/research/hook-bank.md`
   and `reference/skills/daily-content/SKILL.md`.
3. Keep files 14 days, then delete video and covers; keep plans and costs.
4. Transcription: paid API at launch.
5. Hosting: Railway for app, worker, Postgres and file bucket. Stripe for payments. No Supabase.
