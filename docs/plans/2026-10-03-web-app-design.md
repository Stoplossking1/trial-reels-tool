# TrialReelMax: web app spec (simple)

Written 2026-10-03, replaces the detailed v1 (`2026-10-03-web-app-design.v1-detailed.md`, kept for the plumbing:
database, webhooks, uploads). Domain: **trialreelmax.com**.

**The whole product in one line: drop in your video, get 5 variations to post as trial reels.**

Everything that isn't that is cut or hidden.

## 1. Principles

- One job. One button. One screen for the work.
- No options on the way in. The tool makes all choices (hooks, looks, covers, captions, order).
- Every page says what happens next in one short sentence.
- Design: Fastlane's style system (light, black pill buttons, one sparing accent, huge type), see section 7.

## 2. Pages (5 total)

| Path | What |
|---|---|
| `/` | Landing page |
| `/app` | Drop zone, then progress, then the 5 variations, all on this one page |
| `/app/history` | Past runs (a plain list) |
| `/sign-in` | Clerk, Google button only |
| `/terms`, `/privacy` | Legal |

No settings page, no billing page (Stripe's own pages do that), no admin UI at launch (costs go in the database
and a SQL query; admin page is a "should").

## 3. Landing page

1. **Header:** logo left, "Sign in" right. Nothing else.
2. **Hero:** headline about the outcome ("Drop in one video. Get 5 trial reels."), one line under it, one button
   "Try it free" → Google sign-in. Next to or under it: one video turning into 5 phones.
3. **How it works:** three steps, one line each: Drop your video → We make 5 variations → Post them as trial reels.
4. **Proof:** the day 1 result as one sentence and four numbers (1,933 / 218 / 52 / 47 views): the hook is what
   changes the result.
5. **Price:** one card. First run free, then one price per run.
6. **FAQ:** 4 questions max (What's a trial reel? What videos work? How long does it take? What if it fails?).
7. **Footer:** Terms, Privacy, contact.

## 4. The app (`/app`), one page, three states

1. **Drop.** A big box: "Drop your video here". Small line under it: "Vertical, 5-90 seconds, up to 500 MB".
   Bad file: the plain message from R2 right in the box ("This video is sideways. Upload a vertical one.").
2. **Making.** One progress bar and a time estimate. "We'll email you when they're ready."
3. **Ready.** 5 phone-shaped players in posting order. Under each: the hook, a **Copy caption** button,
   **Download** (video + cover together). Above them: **Download all** and the posting guide (R8) in five short lines.

No transcript-fixing step and no options (see question 2).

## 5. Sign-in and money

- **Clerk, Google only.** First sign-in gives 1 free run.
- **Stripe Checkout, one price per run.** When the free run is used, the drop zone says "Next run: £X" and the
  button goes to Stripe Checkout; after paying, the run starts. No packs, no subscription, no credits screen.
- A run that fails or is rejected isn't charged (the payment is only captured when the 5 variations are ready:
  Stripe `capture_method: manual`; cancel the hold on failure). R10.
- Receipts: Stripe emails them.

## 6. Changes to the tool behind it

- **5 variations by default** (was 4). Instagram's trial cap: check the current number before launch (guides say
  about 5, some tools say 20). If it's 5, all 5 can go out the same day.
- Captions burned into the video: **off** by default (fewer things to get wrong without a transcript check;
  see question 2).
- Everything else in the worker stays as built.

## 7. Design: learn from Fastlane

Studied usefastlane.ai on 2026-10-03 (desktop 1440 px and phone 390 px). We take its **style system**, not its
words, logo, images or layout one-for-one.

**What Fastlane does that we follow**

| Pattern | Fastlane | TrialReelMax |
|---|---|---|
| Theme | Light, near-white page (`#FAFAFA`), near-black ink (`#0A0A0A`), grey muted text (`#8A8A90`) | Same idea: page `#FAFAFA`, ink `#0A0A0A`, muted `#8A8A90`, borders `#E8E8EC` |
| One accent, used sparingly | Red-orange (`#FF5A3C`) only on small badges, dots, ticks, and a glow behind the phone | Our accent: **`#FF3D71` (pink-red)**, only on the "New" badge, step dots, ticks and the glow behind the hero phones. Buttons stay black |
| Type | Geist Sans for everything, Geist Mono for small labels | **Geist Sans + Geist Mono** (free, open licence) |
| Hero headline | Huge (about 64 px desktop, 36 px phone), tight leading, centred, the **numbers in italic** | "Drop in **1** video. Get **5** trial reels." with the numbers in italic, 64 / 38 px, weight 500, letter-spacing −2% |
| Above the headline | Small white pill with a red "New" tag | Small pill: "Free first run · no card" |
| Sub-headline | Two lines of grey text ending in a **bold** phrase | "Upload a talking-head video. We write 5 different hooks from what you said and hand back 5 ready-to-post trial reels, **in about 5 minutes**." |
| Main button | Black pill, white text, a small white circle with an arrow on the right; the same button in the nav | Black pill "Try it free" + arrow circle, in the hero and the nav |
| Nav | Floating white pill bar, centred, soft shadow, stays on screen while scrolling | Same: logo left, "Sign in" text + the black "Try it free" pill right |
| Hero visual | One phone mockup with a coloured glow behind it | One phone (your original) and five smaller phones fanning out of it, each playing a variation, glow behind |
| Section labels | Tiny mono uppercase label with a red dot ("● SPOTLIGHT") above a large heading | "● HOW IT WORKS", "● PROOF", "● PRICE", "● QUESTIONS" |
| Proof | A big result stated plainly ("Frank hit 36m views from just one video") beside a phone | "Same video. The hook made it 1,933 views instead of 47." beside four phones with their view counts |
| Results grid | Dark phone cards with view / like / comment counts on the right edge, like the real app | The 5 variations on the results page use the same idea: dark 9:16 cards, the hook on top, the order number |
| How it works | Numbered steps "01 02 03" with one line each | 01 Drop your video · 02 We make 5 variations · 03 Post them as trial reels |
| Pricing | Clean white cards, plan name, one line of who it's for, big price, black button, ticks | **One** card only (we have one price) |
| FAQ | Plain accordion, one open at a time | Same, 4 questions |
| Space and motion | Lots of white space; sections fade and un-blur in as you scroll | Same: 120 px between sections on desktop, 72 px on phone; soft fade-in, nothing that moves on its own except the hero videos |
| Corners | 16 px cards, 24-34 px big panels, full pill buttons | Same: `--radius 16px`, `--radius-lg 24px`, `--radius-xl 34px` |

**What we leave out:** logo walls, Product Hunt badges, testimonials (we don't have them yet, and we don't fake
them), a long features list, Discord/affiliate blocks, and the giant footer of tool pages. Our footer is one line.

**Phone first.** Fastlane stacks everything into one column on phones with the nav pill still on top; we do the
same, and the five hero phones become a sideways swipe row.

## 8. Build order

| # | Step |
|---|---|
| W1 | Landing page + sign-in (Clerk, Google) on Railway |
| W2 | `/app` drop zone → upload to the bucket → worker makes 5 → ready state, emails |
| W3 | Stripe: free first run, then pay per run with hold-and-capture |

## 9. Questions

1. **Price per run** (and currency)? Set after measuring cost, but a launch number is needed for the page.
2. **Burned-in captions:** your doc (R6) says to show the transcript so people can fix misheard words before
   export. With no fixing step, I've turned burned-in captions off by default. OK? (The hooks still come from the
   transcript; a misheard word there would be rare and short.)
