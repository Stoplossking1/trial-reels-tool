# TrialReelMax: web app spec (simple)

Written 2026-10-03, replaces the detailed v1 (`2026-10-03-web-app-design.v1-detailed.md`, kept for the plumbing:
database, webhooks, uploads). Domain: **trialreelmax.com**.

**The whole product in one line: drop in your video, get 5 variations to post as trial reels.**

Everything that isn't that is cut or hidden.

## 1. Principles

- One job. One button. One screen for the work.
- No options on the way in. The tool makes all choices (hooks, looks, covers, captions, order).
- Every page says what happens next in one short sentence.
- Design: learn from Fastlane (usefastlane.ai) (see section 7).

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

Fastlane's site couldn't be opened from the build machine, so the specific layout notes are still to do. What we
take from it is the **approach**, in our own copy and our own visuals (we don't copy their text or graphics):
a headline that promises a big outcome in a short time, a product that does the work for you, very little to read.

To finish this section: send screenshots of the Fastlane pages you like (hero, how it works, pricing), and I'll
write down the layout, type sizes, spacing and colours to follow.

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
3. **Fastlane screenshots** for section 7.
