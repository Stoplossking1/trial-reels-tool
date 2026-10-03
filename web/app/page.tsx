import Image from "next/image";
import { CTA, Footer, JsonLd, Label, Nav, Phone } from "@/components/ui";
import { faq } from "@/lib/faq";
import { original, variants, madeIn } from "@/lib/demo";
import { price, site } from "@/lib/site";

const steps = [
  { n: "01", t: "Drop your video", d: "One vertical talking-head video, straight off your phone." },
  { n: "02", t: "We make 3 variations", d: "3 hooks from your own words, 3 different looks, covers and captions." },
  { n: "03", t: "Post them as trial reels", d: "Post in the order we give you. After 24 hours, keep the winner." },
];

const proof = [
  { hook: "Winning hook", views: "1,933" },
  { hook: "Hook 2", views: "218" },
  { hook: "Hook 3", views: "52" },
  { hook: "Hook 4", views: "47" },
];

function HeroPhones() {
  const five = variants;
  return (
    <div className="relative mx-auto mt-16 flex max-w-5xl items-center justify-center gap-4 px-4 sm:gap-8">
      <div aria-hidden className="pointer-events-none absolute inset-x-10 top-10 -z-10 h-72 rounded-full bg-accent/25 blur-[90px]" />
      <div className="shrink-0">
        <Phone className="w-[120px] sm:w-[170px]" label="Your video">
          {original.cover && <Image src={original.cover} alt="The original video" fill sizes="170px" className="object-cover" priority />}
        </Phone>
      </div>
      <svg className="hidden shrink-0 text-muted sm:block" width="48" height="24" viewBox="0 0 48 24" aria-hidden>
        <path d="M2 12h40M34 4l8 8-8 8" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" />
      </svg>
      <div className="-mr-4 flex snap-x gap-3 overflow-x-auto pb-4 pr-4 sm:mr-0 sm:overflow-visible sm:pr-0">
        {five.map((v, i) => (
          <Phone key={v.order} className="w-[96px] shrink-0 snap-start sm:w-[118px]" label={`#${i + 1}`}>
            <Image src={v.cover} alt={`Variation ${i + 1}: ${v.hook}`} fill sizes="118px" className="object-cover" />
          </Phone>
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  const ld = [
    {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      name: site.name,
      url: site.url,
      applicationCategory: "MultimediaApplication",
      operatingSystem: "Web",
      description: site.description,
      offers: [
        { "@type": "Offer", name: "First run", price: "0", priceCurrency: price.currency.toUpperCase() },
        { "@type": "Offer", name: "Per run", price: (price.cents / 100).toFixed(2), priceCurrency: price.currency.toUpperCase() },
      ],
    },
    { "@context": "https://schema.org", "@type": "Organization", name: site.name, url: site.url, logo: `${site.url}/icon.svg`, email: site.email },
    {
      "@context": "https://schema.org",
      "@type": "HowTo",
      name: "How to make 3 Instagram trial reels from one video",
      step: steps.map((s, i) => ({ "@type": "HowToStep", position: i + 1, name: s.t, text: s.d })),
    },
    {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      mainEntity: faq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
    },
  ];

  return (
    <>
      <JsonLd data={ld} />
      <Nav />
      <main>
        {/* Hero */}
        <section className="px-4 pt-16 text-center sm:pt-24">
          <p className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-line bg-card py-1 pl-1 pr-3 text-xs text-soft shadow-sm">
            <span className="rounded-full bg-accent px-2 py-0.5 text-[11px] font-medium text-white">Free</span>
            Your first run is on us. No card needed.
          </p>
          <h1 className="mx-auto max-w-3xl text-[40px] font-medium leading-[1.02] tracking-[-0.035em] sm:text-[68px]">
            Drop in <em className="font-medium">1</em> video.
            <br />
            Get <em className="font-medium">3</em> trial reels.
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-[17px] leading-relaxed text-muted">
            Upload a talking-head video. We write 3 different hooks from what you said and hand back 3 ready-to-post
            Instagram trial reels, <strong className="font-semibold text-ink">each with its own cover and caption</strong>.
          </p>
          <div className="mt-8 flex justify-center">
            <CTA>Try it free</CTA>
          </div>
          <HeroPhones />
        </section>

        {/* How it works */}
        <section id="how" className="reveal mx-auto mt-28 max-w-5xl px-4 text-center">
          <Label>How it works</Label>
          <h2 className="text-3xl font-medium tracking-tight sm:text-5xl">One upload. That&apos;s the whole job.</h2>
          <ol className="mt-12 grid gap-4 text-left sm:grid-cols-3">
            {steps.map((s) => (
              <li key={s.n} className="rounded-[var(--radius-panel)] border border-line bg-card p-6">
                <span className="font-mono text-sm text-accent">{s.n}</span>
                <h3 className="mt-3 text-lg font-semibold">{s.t}</h3>
                <p className="mt-1 text-soft">{s.d}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Proof */}
        <section className="reveal mx-auto mt-28 max-w-5xl px-4">
          <div className="grid items-center gap-10 rounded-[var(--radius-xl2)] border border-line bg-card p-8 sm:grid-cols-2 sm:p-12">
            <div>
              <Label>Why hooks</Label>
              <h2 className="text-3xl font-medium leading-tight tracking-tight sm:text-4xl">Same video. The hook made it 1,933 views instead of 47.</h2>
              <p className="mt-4 text-soft">
                We posted one video as four trial reels with four different openings. The best got 1,933 views; the others
                got 218, 52 and 47. The first three seconds decide who keeps watching, so that&apos;s what we change.
              </p>
            </div>
            <ul className="grid grid-cols-2 gap-3">
              {proof.map((p, i) => (
                <li key={p.hook} className={`rounded-[var(--radius-card)] p-5 ${i === 0 ? "bg-ink text-white" : "bg-page"}`}>
                  <p className={`font-mono text-[11px] uppercase tracking-wider ${i === 0 ? "text-white/60" : "text-muted"}`}>{p.hook}</p>
                  <p className="mt-2 text-3xl font-medium tracking-tight">{p.views}</p>
                  <p className={`text-sm ${i === 0 ? "text-white/60" : "text-muted"}`}>views in 24h</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* What you get */}
        <section className="reveal mx-auto mt-28 max-w-5xl px-4 text-center">
          <Label>What you get</Label>
          <h2 className="text-3xl font-medium tracking-tight sm:text-5xl">3 variations, ready to post.</h2>
          <ul className="mt-12 grid gap-4 text-left sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["A hook from your words", "Number first, problem first, how-to, a name, a question. Never made up."],
              ["A different look", "Speed, mirror, zoom, colour and fonts change on every variation."],
              ["A cover and a caption", "A frame where you look composed, and a one-line caption to paste."],
              ["The order to post", "Plus a 5-line guide for posting and picking the winner."],
            ].map(([t, d]) => (
              <li key={t} className="rounded-[var(--radius-panel)] border border-line bg-card p-6">
                <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden className="text-accent"><path d="M4 10.5 8 14l8-8" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
                <h3 className="mt-3 font-semibold">{t}</h3>
                <p className="mt-1 text-sm text-soft">{d}</p>
              </li>
            ))}
          </ul>
          <p className="mt-6 text-sm text-muted">Text always stays clear of your face and of Instagram&apos;s buttons. No music added. Made in {madeIn}.</p>
        </section>

        {/* Price */}
        <section id="price" className="reveal mx-auto mt-28 max-w-md px-4 text-center">
          <Label>Price</Label>
          <div className="rounded-[var(--radius-xl2)] border border-line bg-card p-8 shadow-[0_24px_60px_-30px_rgba(0,0,0,.25)]">
            <p className="text-sm text-muted">First run free, then</p>
            <p className="mt-1 text-6xl font-medium tracking-tight">{price.label}</p>
            <p className="text-muted">per video</p>
            <ul className="mx-auto mt-6 max-w-xs space-y-2 text-left text-soft">
              {["3 trial reel variations", "3 hooks from your own words", "Covers, captions and posting order", "A failed run is never charged"].map((x) => (
                <li key={x} className="flex gap-2"><span className="text-accent">✓</span>{x}</li>
              ))}
            </ul>
            <CTA className="mt-8">Make my first 3 free</CTA>
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className="reveal mx-auto mt-28 max-w-2xl px-4">
          <div className="text-center"><Label>Questions</Label></div>
          <h2 className="text-center text-3xl font-medium tracking-tight sm:text-4xl">Good to know</h2>
          <div className="mt-10 divide-y divide-line rounded-[var(--radius-panel)] border border-line bg-card">
            {faq.map((f, i) => (
              <details key={f.q} className="group px-6 py-5" open={i === 0}>
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium">
                  {f.q}
                  <span className="text-muted transition group-open:rotate-45">+</span>
                </summary>
                <p className="mt-3 leading-relaxed text-soft">{f.a}</p>
              </details>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="reveal mx-auto mt-28 max-w-3xl px-4 text-center">
          <h2 className="text-4xl font-medium tracking-tight sm:text-6xl">Your first <em>3</em> are free.</h2>
          <div className="mt-8 flex justify-center"><CTA>Try it free</CTA></div>
        </section>
      </main>
      <Footer />
    </>
  );
}
