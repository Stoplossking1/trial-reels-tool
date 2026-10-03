"use client";

import { useEffect, useRef, useState } from "react";
import { Arrow } from "@/components/ui";
import { IgGradientDefs, InstagramGlyph } from "@/components/icons";
import { handle, madeIn, variants, type Variant } from "@/lib/demo";

type PostState = "idle" | "posting" | "posted";

function VariantCard({ v, state, progress, i }: { v: Variant; state: PostState; progress: number; i: number }) {
  const [copied, setCopied] = useState(false);
  const video = useRef<HTMLVideoElement>(null);
  const copy = async () => {
    try { await navigator.clipboard.writeText(v.caption); setCopied(true); setTimeout(() => setCopied(false), 1200); } catch { /* select text instead */ }
  };
  return (
    <article className={`rise grid min-w-0 content-start gap-2.5 ${state}`} style={{ animationDelay: `${i * 120}ms` }}>
      <div className="phone-frame relative aspect-[9/16] overflow-hidden rounded-[18px] border-4 border-phone bg-phone shadow-[0_20px_44px_-18px_rgba(0,0,0,.5)]">
        <video
          ref={video}
          src={v.video}
          poster={v.cover}
          muted
          loop
          playsInline
          preload="none"
          className="h-full w-full object-cover"
          onMouseEnter={() => video.current?.play().catch(() => {})}
          onMouseLeave={() => video.current?.pause()}
          onClick={(e) => { const el = e.currentTarget; el.muted = false; el.paused ? el.play().catch(() => {}) : el.pause(); }}
        />
        <div className="pov">
          <svg className="ring" viewBox="0 0 46 46" aria-hidden>
            <circle cx="23" cy="23" r="18" fill="none" strokeWidth="4" stroke="rgba(255,255,255,.25)" />
            <circle className="p" cx="23" cy="23" r="18" fill="none" strokeWidth="4" strokeLinecap="round" stroke="url(#iggrad)" style={{ strokeDashoffset: 113 * (1 - progress) }} />
          </svg>
          <span className="done ig-grad">
            <svg width="22" height="22" viewBox="0 0 20 20" aria-hidden><path d="M4.5 10.5 8.5 14.5 15.5 6" stroke="#fff" strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </span>
          <span className="live"><i />Live as trial</span>
        </div>
      </div>
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[11px] tracking-wide text-soft">POST #{v.order}{state === "posted" && <span className="text-muted"> · live</span>}</span>
        <span className={`whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] ${v.pattern === "original" ? "border border-line bg-page text-soft" : "bg-accent/10 text-[#b0103f]"}`}>{v.pattern}</span>
      </div>
      <h2 className="text-[15px] font-semibold leading-snug tracking-tight">{v.hook}</h2>
      <p className="rounded-xl border border-line bg-page px-3 py-2 text-[13px] leading-snug text-soft select-all">{v.caption}</p>
      <div className="flex flex-wrap gap-1.5">
        <button type="button" onClick={copy} className="rounded-full bg-ink px-3 py-1.5 text-xs font-medium text-white">{copied ? "Copied" : "Copy caption"}</button>
        <a href={v.video} download className="rounded-full border border-line bg-card px-3 py-1.5 text-xs font-medium">Download</a>
      </div>
      {v.changes.length > 0 && <p className="text-[11px] leading-relaxed text-muted">{v.changes.join(" · ")}</p>}
    </article>
  );
}

function burst(from: HTMLElement) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const r = from.getBoundingClientRect();
  const host = document.createElement("div");
  Object.assign(host.style, { position: "fixed", left: `${r.left + r.width / 2}px`, top: `${r.top + r.height / 2}px`, pointerEvents: "none", zIndex: "60" });
  const cols = ["#feda75", "#fa7e1e", "#d62976", "#962fbf", "#4f5bd5"];
  for (let i = 0; i < 28; i++) {
    const p = document.createElement("i");
    Object.assign(p.style, { position: "absolute", width: "7px", height: "7px", borderRadius: "2px", background: cols[i % 5] });
    host.appendChild(p);
    const a = Math.random() * Math.PI * 2, d = 60 + Math.random() * 120;
    p.animate(
      [{ transform: "translate(0,0) rotate(0)", opacity: 1 }, { transform: `translate(${Math.cos(a) * d}px,${Math.sin(a) * d - 40}px) rotate(${Math.random() * 360}deg)`, opacity: 0 }],
      { duration: 900 + Math.random() * 500, easing: "cubic-bezier(.2,.8,.3,1)", fill: "forwards" },
    );
  }
  document.body.appendChild(host);
  setTimeout(() => host.remove(), 1600);
}

export function Results() {
  const [states, setStates] = useState<PostState[]>(() => variants.map(() => "idle"));
  const [progress, setProgress] = useState<number[]>(() => variants.map(() => 0));
  const [running, setRunning] = useState(false);
  const [allDone, setAllDone] = useState(false);
  const [checkBack, setCheckBack] = useState("");
  const btn = useRef<HTMLButtonElement>(null);
  const posted = states.filter((s) => s === "posted").length;
  const current = states.findIndex((s) => s === "posting");

  useEffect(() => {
    const d = new Date(Date.now() + 864e5);
    setCheckBack(`${d.toLocaleDateString(undefined, { weekday: "short" })} ${d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`);
  }, [allDone]);

  async function postAll() {
    if (running || allDone) return;
    setRunning(true);
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
    for (let i = 0; i < variants.length; i++) {
      setStates((s) => s.map((x, k) => (k === i ? "posting" : x)));
      const steps = reduce ? 1 : 14;
      for (let k = 1; k <= steps; k++) {
        await wait(60);
        setProgress((p) => p.map((x, j) => (j === i ? k / steps : x)));
      }
      setStates((s) => s.map((x, k) => (k === i ? "posted" : x)));
      await wait(reduce ? 50 : 260);
    }
    if (btn.current) burst(btn.current);
    await wait(450);
    setAllDone(true);
    setRunning(false);
  }

  return (
    <div className="mx-auto max-w-6xl">
      <IgGradientDefs />
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-medium tracking-tight sm:text-4xl">Your trial reels are ready</h1>
          <p className="mt-1 text-sm text-muted">Made in {madeIn} · downloads available for 14 days</p>
        </div>
        <a href="/demo/trialreelmax-demo.zip" download className="inline-flex items-center rounded-full bg-ink py-2 pl-5 pr-2 text-[15px] font-medium text-white shadow-[0_8px_24px_-8px_rgba(0,0,0,.45)]">
          Download all <Arrow />
        </a>
      </div>

      <details className="mt-5 rounded-[var(--radius-card)] border border-line bg-card px-5 py-4 text-sm text-soft" open>
        <summary className="cursor-pointer font-semibold text-ink">How to post these</summary>
        <ol className="mt-2 grid list-decimal gap-1 pl-5">
          <li>Post each one as a trial reel. &ldquo;Share automatically with everyone&rdquo; off.</li>
          <li>Post them in the order shown, with their own cover and caption.</li>
          <li>Don&apos;t go over Instagram&apos;s daily trial limit.</li>
          <li>After 24 hours, compare views.</li>
          <li>Share the top one to your profile only if it has about double the views of the middle one.</li>
        </ol>
      </details>

      <div className="mt-6 grid grid-cols-2 gap-x-4 gap-y-8 md:grid-cols-3 lg:grid-cols-5">
        {variants.map((v, i) => <VariantCard key={v.order} v={v} i={i} state={states[i]} progress={progress[i]} />)}
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-between gap-4 rounded-[18px] border border-line bg-card p-3 pl-4">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <span className="ig-grad h-8 w-8 rounded-full p-[2px]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={variants[variants.length - 1].cover} alt="" className="h-full w-full rounded-full border-2 border-white object-cover" />
          </span>
          {handle}
        </div>
        <p className="max-w-md flex-1 text-[13px] text-soft">Posts all {variants.length} as <b className="text-ink">trial reels</b>, each with its own cover and caption, shown to non-followers first. Spaced out in posting order.</p>
        <button ref={btn} type="button" onClick={postAll} disabled={running || allDone} className="igbtn inline-flex items-center gap-2.5 rounded-full py-3 pl-4 pr-5 text-[15px] font-semibold text-white">
          <InstagramGlyph />
          {allDone ? "Posted" : running ? `Posting ${Math.min(variants.length, current + 1 || posted)} of ${variants.length}` : "Post all as trial reels"}
          <span className="rounded-full bg-white/25 px-2 py-0.5 font-mono text-xs font-medium">{running || allDone ? `${posted}/${variants.length}` : variants.length}</span>
        </button>
      </div>

      {allDone && (
        <div className="rise ig-grad mt-4 rounded-[22px] p-[2px]">
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-[20px] bg-card px-5 py-4">
            <div>
              <h2 className="text-xl font-semibold tracking-tight">All {variants.length} are live as trial reels</h2>
              <p className="mt-1 max-w-xl text-[13px] text-soft">Instagram is showing them to people who don&apos;t follow you. Come back in 24 hours: we&apos;ll compare views and tell you which hook won.</p>
            </div>
            <div className="flex flex-wrap gap-1.5 font-mono text-[11px] text-soft">
              <span className="rounded-full border border-line bg-page px-2.5 py-1">{variants.length} of {variants.length} posted</span>
              <span className="rounded-full border border-line bg-page px-2.5 py-1">non-followers only</span>
              <span className="rounded-full border border-line bg-page px-2.5 py-1">check back {checkBack}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
