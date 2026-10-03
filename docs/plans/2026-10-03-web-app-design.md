# Trial reel tool: web app spec

Written 2026-10-03. Covers milestones M3 (web app) and M4 (money) from `2026-10-03-trial-reels-design.md`.
The product rules live in `docs/ready.md` (R-numbers below point there). The video work is the `worker/` CLI,
already built; the web app wraps it.

"Must" = needed before launch. "Should" = next version.

## 0. Decisions

| Decision | Choice | Why |
|---|---|---|
| Framework | Next.js 15 (App Router, TypeScript), Tailwind CSS, shadcn/ui components | The default stack of most new SaaS apps; fast to build, easy to hire for. |
| Sign-in | **Clerk, Google only** | Replaces Auth.js from the first design. One button, no passwords, no email codes. A Google account per person also makes the free run harder to farm (R10). |
| Payments | **Stripe Checkout** (hosted page) + Stripe Customer Portal for receipts | No card form to build or secure. Apple Pay / Google Pay come for free. |
| Billing model | **Credits.** 1 credit = 1 generation. Sign-up gives 1 free credit. Credits sold in packs, no subscription at launch | Matches "price per generation" (R10). A failed run just gives the credit back, so we never need a Stripe refund. Packs give a volume discount without subscription churn. |
| Database | Railway Postgres, Drizzle ORM | As decided. |
| Files | Railway bucket, presigned URLs, upload straight from the browser (multipart for big files) | 500 MB uploads never pass through our server. |
| Jobs | `runs` table; the Python worker claims with `FOR UPDATE SKIP LOCKED` | As designed. No extra queue service. |
| Live progress | Browser polls `GET /api/runs/:id` every 2 s while a run is active | Simple and reliable on Railway. Server-sent events can come later. |
| Email | Resend: "your versions are ready" and receipts link | People leave during a 5-minute run. |
| Analytics | PostHog (already connected to this account) | Funnel: landing, sign-up, first upload, first download, purchase. |
| Hosting | Railway: `web` (Next.js), `worker` (Python), Postgres, bucket | As decided. |

## 1. Look and feel

Modelled on the patterns that well-known video and creator SaaS tools share (the short-video editors and
caption tools, plus the polish of tools like Linear, Vercel and Stripe). What we take from them:

- **One job per screen.** The landing page sells one thing; the app's home screen is one upload box.
- **Show the output, not the features.** The hero is a real before/after: one video becomes 4 phones side by side.
- **Dark-first, high contrast, one accent colour.** Creator tools are mostly dark because video looks better on
  dark. One bright accent for the main action only.
- **Big drop zone, then a stepper.** Upload → Check words → Making → Ready. Always clear what happens next.
- **Phone-shaped previews.** Every result is shown in a 9:16 frame, the way it will look on Instagram.
- **Honest numbers.** Real run time, real day 1 results (1,933 vs 218, 52, 47 views), no fake logos or counters.

Design tokens (Tailwind theme):

| Token | Value |
|---|---|
| Background | `#0B0B0F` (dark), `#FFFFFF` (light) |
| Surface / card | `#15151C` / `#F6F6F8` |
| Border | `#26262F` / `#E6E6EB` |
| Text | `#F5F5F7` / `#0B0B0F`; muted `#9A9AA5` / `#5E5E6A` |
| Accent (main buttons, progress, links) | `#FF3D71`, hover `#FF5A86` |
| Success / warning / error | `#22C55E` / `#F59E0B` / `#EF4444` |
| Font | Inter for the interface; display headings Inter Tight 600 |
| Radius | 12 px cards, 999 px buttons and pills |
| Spacing | 4 px grid; page max width 1200 px; 16 px side gutter on phones |

Dark by default, follows the system setting, with a toggle in the user menu. Must work at 375 px wide
(most creators will open it on their phone).

## 2. Pages

| Path | Who | What |
|---|---|---|
| `/` | everyone | Landing page (section 3) |
| `/pricing` | everyone | Pricing (section 6), also a section on the landing page |
| `/sign-in`, `/sign-up` | signed out | Clerk, Google button only |
| `/app` | signed in | Home: upload box + recent runs |
| `/app/runs/:id` | owner | One run: steps from transcript check to results |
| `/app/runs` | signed in | All runs (history) |
| `/app/billing` | signed in | Credits, buy more, receipts (Stripe portal link) |
| `/admin` | admins | Runs, real cost vs price, failures, users (section 8) |
| `/terms`, `/privacy`, `/refunds` | everyone | Legal pages (must exist before taking money) |

Signed-in people who open `/` see the landing page with "Open app" instead of "Start free" in the header.

## 3. Landing page

Sections in order. Copy is a first draft in the plain voice of `ready.md`.

1. **Header (sticky).** Logo left. Links: How it works, Results, Pricing, FAQ. Right: "Sign in" (text) and
   "Start free" (accent pill). On phones: logo + "Start free" + menu icon.
2. **Hero.**
   - Headline: "One video in. Four trial reels out."
   - Sub: "Upload a talking-head video. Get 4 versions with different hooks and looks, ready to post as Instagram
     trial reels, so you can see which one strangers actually watch."
   - Button: "Make my first 4 free" → sign-up. Under it, small: "Google sign-in. No card needed."
   - Visual: one phone on the left (the original) with an arrow into four phones on the right, each showing a
     different hook. Autoplaying, muted, looping clips (made by the tool itself). Under 2 MB in total; a still
     poster frame loads first.
3. **Proof strip.** "Day 1 test: the winning hook got 1,933 views. The other three got 218, 52 and 47. Same video,
   different first 3 seconds." With the four hooks as small cards and a view count on each.
4. **How it works.** Three steps with small screenshots: "Upload your video" → "Check the words we heard" →
   "Download 4 versions + covers + captions".
5. **What you get (per version).** Grid of 4 cards: hook from what you actually said; a different look (speed,
   mirror, zoom, colour, fonts); a cover with your mouth closed; a caption ready to paste. Plus "a posting order
   and a guide".
6. **Rules we follow for you.** Short list, each with a tick: text stays clear of Instagram's buttons and your
   face; nothing made up, every hook comes from your words; no music added; never more than 5 a day.
7. **Pricing** (section 6), same component as `/pricing`.
8. **FAQ.** What's a trial reel? Does it work for any video? (vertical, talking, 5-90 s.) Will Instagram see these
   as copies? (We don't promise that; see R9.) What happens if a run fails? (Credit back automatically.)
   Do you post for me? (No.) How long does it take? (Measured number from M5.) What do you keep? (Videos 14 days.)
9. **Final call to action.** "Your first 4 are free." + button.
10. **Footer.** Pricing, FAQ, Terms, Privacy, Refunds, contact email, © line.

Must: Lighthouse performance ≥ 90 on phone, all text real HTML (not baked into images), Open Graph image and
title for link previews, `sitemap.xml`, `robots.txt`.

## 4. Sign-in and sign-up (Clerk)

- Clerk with **Google as the only sign-in method**: no email/password, no email codes, no other social logins.
  Set in the Clerk dashboard; the app only renders Clerk's `<SignIn>` / `<SignUp>` components, styled with our
  tokens (Clerk `appearance` prop), on a centred card with the logo and one line: "Sign in to make your trial reels."
- Middleware (`clerkMiddleware`) protects `/app/*`, `/admin/*` and `/api/*` except webhooks.
- After sign-up the person lands on `/app` with the upload box and a banner: "You have 1 free run."
- **Our user record.** Clerk webhook `user.created` (verified with Svix) inserts a row into `users` with the Clerk
  user id and email, and grants 1 free credit. `user.deleted` marks the row deleted and deletes their files.
  As a fallback, the first signed-in API request creates the row if the webhook hasn't arrived yet. The free
  credit is granted exactly once per Clerk user id (unique ledger entry, see section 7).
- **Free-run abuse (R10).** One free credit per Google account. Should: also block the free credit when the same
  Google email was deleted and signed up again within 90 days (keep a hash of deleted emails).
- Admins: Clerk `publicMetadata.role = "admin"`, set by hand in the Clerk dashboard.

## 5. The app

### 5.1 Home `/app`

- Top bar: logo, "New run" (accent), credits pill ("2 credits", click → billing), avatar menu (Billing, Theme,
  Sign out).
- Centre: **the drop zone.** "Drop a vertical video here, or browse." Under it the rules in one line:
  "Vertical (9:16) · 5 to 90 seconds · MOV or MP4 · up to 500 MB". On phones the whole box is the file picker
  (opens Camera Roll).
- Options under the drop zone (collapsed under "Options"): own hook (text, optional), "My video has text in it"
  (don't mirror), captions on/off (default on), number of versions (2-5, default 4).
- Recent runs below: cards with the first frame, date, status chip, number of versions.
- **Empty state** (first visit): the drop zone plus a short 3-step "how it works" row.
- **No credits:** the drop zone still accepts the file, then shows a "Buy credits to continue" sheet. The upload
  isn't lost: it waits on the run page.

### 5.2 Upload

- The browser checks what it can before uploading (file type, size, length and orientation from the `<video>`
  element's metadata) and shows the plain R2 messages straight away ("This video is sideways. Upload a vertical
  one."). The worker checks again; the browser check is only for speed.
- Upload straight to the bucket with presigned multipart URLs (10 MB parts, 4 at a time, retry each part 3 times).
  Shows a progress bar, MB done, and time left. Closing the tab warns "Upload in progress".
- When the upload completes: `POST /api/runs` creates the run and **reserves** 1 credit (section 7), then the page
  goes to `/app/runs/:id`.

### 5.3 Run page `/app/runs/:id`

A stepper at the top: **Upload → Check words → Making → Ready.** The page polls the run every 2 s.

1. **Checking video** (seconds): spinner, "Checking your video…". If rejected: the R2 message in a red card,
   "No credit used", and "Upload another".
2. **Check words** (R6 captions): the transcript as words in sentences. Click a word to fix it inline (Enter to
   save, Tab to the next). Words below a confidence threshold are underlined amber. A play button next to each
   sentence plays that bit of the video. Buttons: "Looks right, make my versions" (accent). Should: "Skip
   checking next time".
3. **Making** (minutes): a list of live steps from the worker (finding your face, writing hooks, making version 1
   of 4, …) with ticks, and an estimate ("about 4 minutes left") based on video length and measured averages.
   "We'll email you when it's ready. You can close this tab."
4. **Ready**: see 5.4.
- **Failed** (our fault): "Something went wrong on our side. Your credit is back." + "Try again" (re-queues the same
  upload, no new upload needed) + support email.

### 5.4 Results (R3, R7, R8)

- Top: "Your 4 trial reels" + "Download all (.zip)" + run time ("Made in 3 min 40 s").
- **Posting guide** (R8) in a card at the top, collapsible, open the first time. The 5 rules word for word.
- **Versions in posting order**, one card each, in a row of phone frames on desktop, a vertical list on phones:
  - the video (9:16 player, tap to play with sound)
  - "Post #1 · today" order badge (with at most 5 a day, versions 6+ say "tomorrow")
  - the hook text and its pattern chip ("number first")
  - "What changed" as chips (1.2x, mirrored, Jost captions, …)
  - caption in a box with **Copy** button
  - cover thumbnail with **Download cover**
  - **Download video**
  - On phones: **Share** (Web Share API) to send the video straight to Instagram on the phone.
- Should: "Log your 24-hour views" fields on each card, then a small table that applies R8 rule 5 ("Share the top
  one only if it has about double the middle one").
- Files expire after 14 days: shown as "Downloads available until 17 Oct".

### 5.5 Runs list `/app/runs`

Table on desktop / cards on phones: thumbnail, date, length, status, versions, expiry. Click → run page.

### 5.6 Billing `/app/billing`

Credits balance, the packs (same component as pricing), a list of credit changes (free credit, purchase,
run used, run refunded) and "Receipts and invoices" → Stripe Customer Portal.

## 6. Pricing

The price per credit is set after measuring real run cost (R10, M5). The page and code take prices from Stripe,
so changing them needs no deploy. Placeholder structure:

| Pack | Credits | Price | Shown as |
|---|---|---|---|
| Free | 1 | £0 | "Your first run" (given at sign-up) |
| Single | 1 | £X | |
| Creator | 5 | £4.5X | "Save 10%" |
| Studio | 15 | £12X | "Best value · save 20%" (highlighted) |

- Pricing cards: three columns (Single, Creator highlighted as most popular or Studio as best value), each with
  price, price per run, what one run gives you (4 versions + covers + captions + posting guide), and a button.
- Under the cards: "A run that fails gives your credit back automatically. Credits don't expire."
- Should: a monthly plan once we see repeat use.

## 7. Payments (Stripe)

- **Products:** one Stripe Product per pack, one-time Prices. `metadata.credits` on each Price says how many
  credits it gives. The app reads active Prices from Stripe (cached 5 min).
- **Buying:** `POST /api/checkout { priceId }` creates a Checkout Session (`mode: "payment"`) with
  `client_reference_id` = our user id, the Stripe Customer for that user (created on first purchase, id saved),
  `success_url = /app/billing?paid={CHECKOUT_SESSION_ID}` (or back to the waiting run), `cancel_url` back where
  they were. Automatic tax and promotion codes on.
- **Fulfilment only by webhook.** `checkout.session.completed` (signature verified, idempotent on the event id)
  adds the credits. The success page polls until the credits appear ("Adding your credits…"), never adds credits
  itself. Also handle `checkout.session.async_payment_succeeded`; `charge.refunded` (a refund we issue by hand)
  removes unused credits.
- **Credit ledger** (never a bare balance column): every change is a row; balance = sum.

  ```
  credit_ledger  id, user_id, delta (+1/-1/+5…), reason ('signup_free' | 'purchase' | 'run_reserve' |
                 'run_release' | 'refund' | 'admin'), run_id null, stripe_event_id null unique, created_at
                 unique (user_id) where reason = 'signup_free'
  ```

- **Charging a run (R10):** when a run is created, insert `run_reserve -1` in the same transaction that creates
  the run (fails if the balance would go below 0). If the run ends `rejected` or `failed`, insert `run_release +1`.
  The free credit is just the first credit, so "a failed run doesn't use up the free one" holds automatically.
- **Customer Portal** for receipts and invoices (no subscriptions to manage yet).

## 8. Admin `/admin`

- Runs table: user, status, video length, run time, versions delivered/dropped, and **real cost** next to
  **price** (R10): transcript $, Claude $, compute seconds × rate, storage. Filters: failed, rejected, last 7 days.
- Averages: cost per run, cost per minute of video, run time per minute of video, margin per pack.
- A run's detail: the worker's `report.json` (hooks rejected and why, versions dropped and why), the files.
- Users: email, credits, runs, purchases. Action: grant credits (writes an `admin` ledger row with a note).

## 9. Data model (Postgres, Drizzle)

Changes to the first design: users keyed by Clerk id; credits in a ledger.

```
users          id (uuid), clerk_user_id unique, email, stripe_customer_id, created_at, deleted_at
credit_ledger  as in section 7
runs           id, user_id, status, error_code, error_message, input_key, input_meta jsonb,
               own_hook, has_text, captions_on, n_versions,
               transcript jsonb, transcript_fixed jsonb, progress jsonb (steps + ETA),
               report jsonb, cost jsonb, worker_id, claimed_at, heartbeat_at,
               created_at, started_at, finished_at, expires_at
versions       id, run_id, post_order, hook, pattern, caption, what_changed jsonb,
               video_key, cover_key, duration_s
stripe_events  id (Stripe event id), type, received_at          -- idempotency
```

Run statuses: `uploading → queued_check → checking → awaiting_transcript → queued_make → making → done`,
or `rejected` / `failed`. The worker gets two job types: **check** (validate + transcribe + face track, stops at
`awaiting_transcript`) and **make** (everything after the user confirms the words). A worker that stops sending
heartbeats for 2 minutes has its job re-queued once; a second loss marks the run `failed` (credit back).

## 10. API (Next.js route handlers)

| Route | Does |
|---|---|
| `POST /api/uploads` | Presigned multipart upload URLs for a new file (checks size and type) |
| `POST /api/runs` | Create run from a finished upload + options; reserves 1 credit; queues **check** |
| `GET /api/runs/:id` | Status, progress, transcript, versions (owner only) |
| `POST /api/runs/:id/transcript` | Save fixed words; queues **make** |
| `POST /api/runs/:id/retry` | Re-queue a failed run (reserves again) |
| `GET /api/runs/:id/download/:versionId?file=video\|cover` | Short-lived signed download URL |
| `GET /api/runs/:id/zip` | Zip of all versions, covers, captions and the guide |
| `POST /api/checkout` | Stripe Checkout Session |
| `POST /api/portal` | Stripe Customer Portal session |
| `POST /api/webhooks/stripe` | Credits from payments (signature checked) |
| `POST /api/webhooks/clerk` | User created/deleted (Svix signature checked) |

All `/api/*` except webhooks need a Clerk session, and check the run belongs to the caller.

## 11. Emails (Resend)

- Versions ready: "Your 4 trial reels are ready" + link to the run page + "downloads until 17 Oct".
- Run failed: "Something went wrong. Your credit is back." + retry link.
- Stripe sends payment receipts itself.

## 12. Analytics (PostHog)

Events: `landing_viewed`, `signup_started`, `signup_completed`, `upload_started`, `upload_rejected` (with reason),
`transcript_confirmed`, `run_ready` (with run time), `video_downloaded`, `caption_copied`, `checkout_started`,
`purchase_completed`, `run_failed`. Main funnel: landing → sign-up → first upload → first download → purchase.
No video content or transcripts are sent to analytics.

## 13. Not in this version

Teams, subscriptions, posting to Instagram, an in-browser video editor, other sign-in methods, languages other
than English.

## 14. Ready checklist (web app)

- [ ] Landing page on a phone: loads fast (Lighthouse ≥ 90), hero shows the real 1-into-4 clips, every link works.
- [ ] Sign up with Google → lands on `/app` with 1 free credit. No other sign-in method is offered.
- [ ] Upload a 300 MB phone video on a phone over Wi-Fi: progress bar, no timeout, resumes a failed part.
- [ ] Sideways, 3-minute and silent videos: plain message, credit still there.
- [ ] Fix a word on the transcript screen → the burned-in captions use the fixed word.
- [ ] Close the tab while making → email arrives → results page shows 4 versions in posting order, with guide,
      what changed, covers, copyable captions, downloads and zip.
- [ ] Free run used → next upload asks to buy → Stripe Checkout (test card) → credits appear → run starts.
- [ ] Kill the worker mid-run → run marked failed after retry → credit back → "Try again" works.
- [ ] Paying twice with the same webhook event adds credits once.
- [ ] Admin shows each run's real cost next to its price.
- [ ] Downloads stop working after 14 days; files are gone from the bucket.

## 15. Build order

| # | Step | Done when |
|---|---|---|
| W1 | Next.js app, design tokens, landing page with placeholder clips, legal pages | Deployed on Railway, looks right on phone and desktop |
| W2 | Clerk (Google only), users table + webhook, protected `/app` | Sign up and sign in work; user row and free credit created |
| W3 | Upload (presigned multipart), runs table, worker job loop (check/make), run page with stepper and polling | A real video goes through end to end in the browser |
| W4 | Transcript fix screen, results page, zip, emails | Checklist items for the run flow pass |
| W5 | Stripe products, Checkout, webhook, ledger, billing page, portal | Pay with a test card; failed run returns credit |
| W6 | Admin, PostHog, cleanup job (14 days), hero clips made by the tool | Whole checklist ticked |

## 16. Open questions

1. **Product name and domain.** The spec says "the tool". What's it called, and which domain?
2. **Currency.** Pounds, dollars or euros first? (Stripe can show local prices later.)
3. **Pack sizes.** Are 1 / 5 / 15 credits right, or do you want a monthly plan from day one?
4. **Accent colour / brand.** Is there an existing brand (your account, apmode) to match? Otherwise the pink above.
5. **Hero clips.** OK to use your own day 1 video (and its real view counts) on the landing page?
