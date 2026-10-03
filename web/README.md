# TrialReelMax website (demo)

Landing page, upload page with the loading sequence, results page with the mocked "Post all as trial reels" flow.
Nothing is processed: any uploaded video plays the ~15 s loading sequence, then shows the 5 hardcoded videos.

## Swap in the demo videos

Put the files in `public/demo/` with these names (see `public/demo/README.md`):

- `1.mp4` … `4.mp4`: the 4 variations, in posting order; `5.mp4`: the cleaned-up original
- `1.jpg` … `5.jpg`: a cover frame for each (the ones there now are temporary stills)
- `trialreelmax-demo.zip` (optional): for "Download all"

Hooks, captions, pattern labels and the Instagram handle shown on the page: `lib/demo.json`.
Price and site URL: `lib/site.ts` (or env `PRICE_CENTS`, `PRICE_CURRENCY`, `NEXT_PUBLIC_SITE_URL`).

## Run

```bash
npm install
npm run dev          # http://localhost:3000
npm run build && npm start
```

## Deploy (Railway)

New service from this repo, root directory `web`. Build `npm run build`, start `npm start` (Railway sets `PORT`).
Set `NEXT_PUBLIC_SITE_URL=https://trialreelmax.com`, then add the custom domain in the service settings.

## SEO

Titles and descriptions, Open Graph image, `sitemap.xml`, `robots.txt` (the `/app` demo pages are not indexed),
structured data on the home page (app, offers, how-to, FAQ) and `public/llms.txt` for AI search tools.
