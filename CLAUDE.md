# TrialReelMax: handoff

Read this first. It is the full context from the cloud session that built this repo (2026-10-03), written for
Claude Code on Jordan's own computer.

## What this is

**TrialReelMax** (domain: trialreelmax.com, not deployed yet). One line: *drop in your video, get variations to
post as Instagram trial reels*, each with a different hook (from what you actually said), a different look, its own
cover and caption, so you can see which one strangers watch.

Owner: Jordan (Instagram **@jordanbuilds**). Repo: `https://github.com/Stoplossking1/trial-reels-tool`.

There are two separate things in the repo:

| Folder | What | State |
|---|---|---|
| `web/` | The website: landing page + a **mocked demo** (upload → 30 s fake generation → 3 results → mocked "Post all as trial reels") | Done, used for demos. Nothing is processed. |
| `worker/` | The real video tool (Python CLI): one video in, checked trial-reel variants out | Built and tested on a synthetic clip; not yet run end to end with real API keys |

## How Jordan wants to work (important)

- **Keep it simple.** "We do one thing simply." Don't add features, options or pages that weren't asked for.
- **Do exactly what's asked.** When the task is the website/demo, don't touch `worker/`. Don't re-render videos or
  "fix" the tool unless asked. (In the cloud session, changing the worker during a website task upset him.)
- **Show designs before building them** when it's a visual change (the cloud session used an artifact page for
  approval; locally, a screenshot or a running page works).
- Short, plain answers. He's on his phone a lot.
- Never copy competitors' copy or designs verbatim (asked once; declined for copyright reasons). Style inspiration
  is fine: the site's look is learned from usefastlane.ai.

## Run the demo website (the main thing)

Needs Node 20+ (built with Node 22, Next.js 16, React 19, Tailwind 4).

```bash
git clone https://github.com/Stoplossking1/trial-reels-tool.git
cd trial-reels-tool/web
npm install
npm run dev            # http://localhost:3000
```

The demo flow Jordan shows: open **http://localhost:3000/app**, choose any video file → the 30-second loading
sequence plays → it opens `/app/results` with the 3 variants → press **Post all as trial reels** (Instagram
gradient) → rings, checks, "Live as trial" badges, confetti, "All 3 are live" panel. After that he shows a
screenshot of his real Instagram trial reels.

Production build: `npm run build && npm start` (all pages are static).

### Where the demo content lives

- `web/public/demo/1.mp4`, `2.mp4`, `3.mp4`: Jordan's 3 real trial reels (720p), in posting order:
  1. "My app made $23K. Then it got cloned" (number first)
  2. "A Turkish studio cloned my app" (named thing)
  3. "How I got a copycat app taken down" (how to)
  Source: Google Drive folder `https://drive.google.com/drive/folders/1iB-pqdf5Zye0L_6BgOJP7NeSeOBarPFe`
  (files `trial-2-number-first.mp4`, `trial-4-turkish-studio.mp4`, `trial-5-how-i-did-it.mp4`).
- `web/public/demo/1.jpg`–`3.jpg`: covers (frame at 1 s); `original.jpg`: "your video" still on the landing page.
- `web/public/demo/trialreelmax-demo.zip`: what "Download all" gives (3 videos, covers, captions).
- `web/lib/demo.json`: hooks, pattern labels, captions (written by Claude from the hooks; Jordan may replace them),
  the handle `@jordanbuilds`, "made in" text. The number of variants shown everywhere follows this list.

### Web code map

- `app/page.tsx`: landing page (hero "Drop in 1 video. Get 3 trial reels.", how it works, the day 1 proof
  1,933 vs 218/52/47 views, what you get, price card, FAQ, final CTA). Jordan won't show this or pricing in demos.
- `app/app/UploadFlow.tsx`: drop zone + the 30 s loading sequence (ticks of 100 ms; upload 0-6 s, hearing 6-10 s,
  face 10-13 s, hooks 13-19 s, variations 19-30 s), then `router.push("/app/results")`.
- `app/app/results/Results.tsx`: result cards (video, hook, pattern, copy caption, download), posting guide,
  and the mocked post-to-Instagram flow with confetti.
- `components/ui.tsx` (nav, footer, buttons, phone frame), `components/AppNav.tsx`, `components/icons.tsx`.
- `app/globals.css`: design tokens + the loading/posting animations.
- SEO: `app/layout.tsx` (metadata), `app/opengraph-image.tsx`, `app/sitemap.ts`, `app/robots.ts` (`/app` not
  indexed), JSON-LD on the home page (SoftwareApplication, Organization, HowTo, FAQPage), `public/llms.txt`.
- `lib/site.ts`: name, URL, price (placeholder **$9/video** via `PRICE_CENTS`/`PRICE_CURRENCY` env).
- `app/terms`, `app/privacy`: **placeholders**.

### Design system (approved by Jordan)

Learned from usefastlane.ai's style, our own copy/visuals. Light only. Page `#FAFAFA`, ink `#0A0A0A`, muted
`#8A8A90`, lines `#E8E8EC`, one accent `#FF3D71` used only on small details (dots, ticks, the hero glow). Black pill
buttons with a white arrow circle. Floating pill nav. Geist + Geist Mono. Huge hero type with numbers in italic.
Instagram's gradient appears **only** on the post-to-Instagram button and its states.

## The real tool (`worker/`)

Python 3.11+, FFmpeg. Spec: `docs/ready.md` (Jordan's product rules, "R" numbers) and
`docs/plans/2026-10-03-trial-reels-design.md` (how it's built).

```bash
# macOS
brew install ffmpeg
# Linux: sudo apt-get install ffmpeg libegl1 libgles2   (MediaPipe needs EGL)
cd worker
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q                      # ~40 tests, builds a synthetic clip, no keys needed (~4 min)
```

Run on a video:

```bash
export DEEPGRAM_API_KEY=...              # transcript with word times
export ANTHROPIC_API_KEY=...             # hooks + captions (model claude-opus-5-5)
trialreels transcribe in.MOV --out out/t.json      # optional: fix misheard words in the JSON
trialreels run in.MOV --out out/run --versions 3 --transcript out/t.json
```

Options: `--versions 1-5`, `--hook "own hook"`, `--has-text` (never mirror), `--no-captions`, `--offline` (no
Claude: hooks cut from the transcript), `--hooks-file h.json` / `--captions-file c.json` (hand-written candidates,
still checked), `--track` (reuse a face track). Output: `01_<pattern>.mp4`, `_cover.jpg`, `_caption.txt` in posting
order, `README.md` (download page), `report.json` (costs, timings, dropped versions and why).

Pipeline: validate → transcribe (Deepgram) + safe cut points from audio → face/hands track (MediaPipe, square crops
of the tall frame) → hooks/captions (Claude writes, code rejects numbers/names not said in the video) → looks
(speed 1.15-1.25x, mirror, zoom capped so hands/face stay in frame, colour, font, caption size, hook style, trim,
export; every pair differs in ≥3) → plan (text in safe area x75-1005 y270-1540, nothing right of x900 below
y1230, never on the face, hook 1.5-3 s, captions 1-4 words ≥1.2 s) → render (FFmpeg, text drawn after the mirror,
pitch kept, no music) → checks on plan and file → posting order.

**Fonts.** Jost + Inter (open licence) are in git. Jordan's licensed fonts are **not** in git and must be copied
into `worker/fonts/` with exact names (see `worker/fonts/README.md`): Instagram Sans (`Instagram_Sans*.ttf`,
`Instagram_Sans_Headline.otf`), `SF-Pro-Display-{Regular,Medium,Bold}.otf`,
`Helvetica-Neue-{Roman,Medium,Bold,Heavy}.otf`. Jordan says his licences cover this use. The tool only uses
families whose files are present.

**Test videos (not in git, too big):** Jordan's long talking head (`AE3CD63E-6941-4C1B-AD75-DE5BEBE1A72E.MOV`,
348 MB, 2 min 47 s, Drive file id `1sB9_u3FiDTcmL_hOgsLC7t16x4_i87Ax`). Put test videos in `fixtures/raw/`.

## Decisions already made (don't re-ask)

- Name/domain: TrialReelMax / trialreelmax.com. Handle @jordanbuilds.
- Demo: 3 variants (not 5), 30-second fake generation, no pricing shown in demos.
- No maximum video length (the 90 s limit was removed). Min 5 s, vertical 9:16, MOV/MP4, ≤500 MB.
- Future real app: Railway (hosting, Postgres, bucket), **Clerk with Google sign-in only**, Stripe Checkout,
  one price per run, card only charged when the run succeeds. Paid speech-to-text API at launch.
  Specs: `docs/plans/2026-10-03-web-app-design.md` (simple version) and `...v1-detailed.md` (plumbing).
- Files kept 14 days.

## Open items / known issues

1. **Not deployed.** To put the site on trialreelmax.com: Railway service from this repo, root `web`, build
   `npm run build`, start `npm start`, env `NEXT_PUBLIC_SITE_URL=https://trialreelmax.com`, add the domain.
2. **Instagram daily trial cap** is unsettled (guides say ~5, Reeleaze says 20). The site says "Instagram's daily
   trial limit" without a number. Check Instagram's help page before stating one.
3. Price ($9) and terms/privacy pages are placeholders.
4. The worker has never run with real Deepgram/Claude keys; those calls are tested with faked responses.
5. A worker change (shrinking the hook font step by step to fit clear of the face, in `worker/trialreels/plan.py`,
   `clear_slot` + size loop in `build`) got committed even though Jordan had rejected that edit mid-run. He was
   told; he hasn't said whether to revert it. Ask before reverting.
6. The GitHub default branch may still be `claude/nifty-faraday-e082ws`; `main` has the same commits. Jordan
   can switch the default to `main` in repo settings and delete the old branch.
7. Competitor to know: **Reeleaze** (reeleaze.com), "Test more hooks. Post the winners."; renders trial-reel
   variants from your clips and hook lines and auto-posts via the Instagram API. Our angle: hooks from your own words,
   from one video, checked against the safe area.

## Where things are

```
CLAUDE.md                     this file
docs/ready.md                 Jordan's product rules (R1-R11)
docs/plans/                   build design, web app specs
web/                          Next.js site + demo (see above)
worker/                       Python video tool (see above)
fixtures/raw/                 test videos go here (git-ignored)
```
