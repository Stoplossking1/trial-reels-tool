/** Everything the marketing pages and SEO share. Change copy and price here. */
export const site = {
  name: "TrialReelMax",
  domain: "trialreelmax.com",
  url: (process.env.NEXT_PUBLIC_SITE_URL || "https://trialreelmax.com").replace(/\/$/, ""),
  tagline: "Drop in 1 video. Get 5 trial reels.",
  description:
    "Upload one talking-head video and get 5 ready-to-post Instagram trial reels, each with a different hook written from what you said, its own look, cover and caption. First run free.",
  email: process.env.NEXT_PUBLIC_CONTACT_EMAIL || "hello@trialreelmax.com",
  variations: 5,
};

/** One price per run. Set PRICE_CENTS / PRICE_CURRENCY on Railway; the page and Stripe both read these. */
export const price = {
  cents: Number(process.env.PRICE_CENTS || 900),
  currency: (process.env.PRICE_CURRENCY || "usd").toLowerCase(),
  get label() {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: this.currency, maximumFractionDigits: this.cents % 100 ? 2 : 0 }).format(this.cents / 100);
  },
};
