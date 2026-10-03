import Link from "next/link";

export function Arrow() {
  return (
    <span aria-hidden className="ml-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-white text-ink">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6h8M6.5 2.5 10 6l-3.5 3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
    </span>
  );
}

export function CTA({ href = "/app", children = "Try it free", className = "" }: { href?: string; children?: React.ReactNode; className?: string }) {
  return (
    <Link href={href} className={`inline-flex items-center rounded-full bg-ink py-2 pl-5 pr-2 text-[15px] font-medium text-white shadow-[0_8px_24px_-8px_rgba(0,0,0,.45)] transition hover:bg-black/85 ${className}`}>
      {children}
      <Arrow />
    </Link>
  );
}

export function Label({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-line bg-card px-3 py-1 font-mono text-[11px] uppercase tracking-[0.12em] text-soft">
      <span className="h-1.5 w-1.5 rounded-full bg-accent" />
      {children}
    </p>
  );
}

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 text-[15px] font-semibold tracking-tight">
      <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden>
        <rect x="1" y="1" width="12" height="20" rx="3" fill="#0a0a0a" />
        <rect x="9" y="4" width="12" height="17" rx="3" fill="#ff3d71" stroke="#fafafa" strokeWidth="1.5" />
      </svg>
      TrialReelMax
    </Link>
  );
}

export function Nav() {
  return (
    <header className="sticky top-3 z-50 px-4">
      <nav className="mx-auto flex max-w-3xl items-center justify-between rounded-full border border-line/70 bg-white/80 py-2 pl-5 pr-2 shadow-[0_8px_30px_-12px_rgba(0,0,0,.18)] backdrop-blur">
        <Logo />
        <div className="flex items-center gap-4">
          <Link href="/#how" className="hidden text-sm text-soft hover:text-ink sm:block">How it works</Link>
          <Link href="/#price" className="hidden text-sm text-soft hover:text-ink sm:block">Price</Link>
          <CTA className="!py-1.5 !text-sm">Try it free</CTA>
        </div>
      </nav>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="mx-auto mt-24 flex max-w-6xl flex-col items-center justify-between gap-4 border-t border-line px-4 py-10 text-sm text-muted sm:flex-row">
      <Logo />
      <div className="flex flex-wrap items-center justify-center gap-5">
        <Link href="/#faq" className="hover:text-ink">FAQ</Link>
        <Link href="/terms" className="hover:text-ink">Terms</Link>
        <Link href="/privacy" className="hover:text-ink">Privacy</Link>
        <a href="mailto:hello@trialreelmax.com" className="hover:text-ink">Contact</a>
      </div>
      <p>© {new Date().getFullYear()} TrialReelMax</p>
    </footer>
  );
}

/** A 9:16 phone frame. Children fill the screen. */
export function Phone({ children, className = "", label }: { children?: React.ReactNode; className?: string; label?: string }) {
  return (
    <div className={`relative aspect-[9/16] overflow-hidden rounded-[22px] border-[5px] border-phone bg-phone shadow-[0_24px_60px_-20px_rgba(0,0,0,.45)] ${className}`}>
      {children}
      {label && <span className="absolute left-2 top-2 rounded-full bg-black/55 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-white backdrop-blur">{label}</span>}
    </div>
  );
}

export function JsonLd({ data }: { data: object }) {
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />;
}
