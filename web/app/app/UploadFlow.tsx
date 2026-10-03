"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Arrow } from "@/components/ui";
import { UploadIcon } from "@/components/icons";
import { variants } from "@/lib/demo";

/**
 * Demo upload. Takes any video, plays the approved loading sequence (30 s), then opens the hardcoded results.
 * Phases (ticks of 100 ms): upload 0-60, hearing 60-100, face 100-130, hooks 130-190, variations 190-300.
 */
const T = 300;
const PHASES = ["Uploading your video", "Hearing what you said", "Finding your face, so text stays clear of it", "Writing hooks from your words", "Making the variations"];

function fmtMB(bytes: number) {
  return Math.max(1, Math.round(bytes / 1e6));
}

export function UploadFlow() {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<{ name: string; size: number; url: string } | null>(null);
  const [error, setError] = useState("");
  const [drag, setDrag] = useState(false);
  const [t, setT] = useState(0);

  const start = useCallback((f: File) => {
    setError("");
    if (!f.type.startsWith("video/") && !/\.(mov|mp4)$/i.test(f.name)) {
      setError("This file isn't a video we can read. Upload an MOV or MP4.");
      return;
    }
    if (f.size > 500e6) {
      setError("This video is over 500 MB.");
      return;
    }
    setFile({ name: f.name, size: f.size, url: URL.createObjectURL(f) });
    setT(0);
  }, []);

  useEffect(() => {
    if (!file) return;
    const beforeUnload = (e: BeforeUnloadEvent) => { if (t < 60) e.preventDefault(); };
    window.addEventListener("beforeunload", beforeUnload);
    return () => window.removeEventListener("beforeunload", beforeUnload);
  }, [file, t]);

  useEffect(() => {
    if (!file) return;
    if (t >= T) {
      const id = setTimeout(() => router.push("/app/results"), 900);
      return () => clearTimeout(id);
    }
    const id = setTimeout(() => setT((x) => x + 1), 100);
    return () => clearTimeout(id);
  }, [file, t, router]);

  if (!file) {
    return (
      <div className="mx-auto max-w-xl">
        <h1 className="text-center text-3xl font-medium tracking-tight sm:text-4xl">Drop in your video</h1>
        <p className="mt-2 text-center text-muted">We&apos;ll hand back 5 trial reels with their own hooks, covers and captions.</p>
        <label
          htmlFor="video"
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files?.[0]; if (f) start(f); }}
          className={`mt-8 grid cursor-pointer justify-items-center gap-3 rounded-[var(--radius-panel)] border-[1.5px] border-dashed bg-card px-6 py-14 text-center transition ${drag ? "border-accent bg-accent/5" : "border-[#cfcfd6] hover:border-ink/40"}`}
        >
          <span className="grid h-14 w-14 place-items-center rounded-2xl border border-line bg-page"><UploadIcon /></span>
          <span className="text-xl font-medium tracking-tight">Drop your video here</span>
          <span className={`text-sm ${error ? "font-medium text-[#c2183f]" : "text-muted"}`} role={error ? "alert" : undefined}>
            {error || "Vertical (9:16), at least 5 seconds, MOV or MP4, up to 500 MB"}
          </span>
          <span className="mt-2 inline-flex items-center rounded-full bg-ink py-2 pl-5 pr-2 text-[15px] font-medium text-white shadow-[0_8px_24px_-8px_rgba(0,0,0,.45)]">
            Choose a video <Arrow />
          </span>
          <input ref={input} id="video" type="file" accept="video/mp4,video/quicktime,.mov,.mp4" className="sr-only" onChange={(e) => { const f = e.target.files?.[0]; if (f) start(f); }} />
        </label>
      </div>
    );
  }

  const p = Math.min(1, t / T);
  const step = t <= 60 ? 0 : t <= 100 ? 1 : t <= 130 ? 2 : t <= 190 ? 3 : 4;
  const done = t >= T;
  const mb = fmtMB(file.size);
  const hookIdx = Math.min(4, Math.floor((t - 130) / 12));
  const made = Math.min(5, Math.floor((t - 190) / 22));
  const eta = done ? "done" : t <= 60 ? `${Math.max(0, Math.ceil((60 - t) / 10))} s` : `about ${step === 4 ? Math.max(1, 5 - made) : 6 - step} min left`;

  return (
    <div className="mx-auto grid max-w-xl gap-4 rounded-[var(--radius-panel)] border border-line bg-card p-5 shadow-[0_24px_60px_-30px_rgba(0,0,0,.25)] sm:p-6" aria-live="polite">
      <div className="flex items-center gap-3">
        <video src={file.url} muted playsInline className="aspect-[9/16] w-9 shrink-0 rounded-md bg-phone object-cover" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">{file.name}</p>
          <p className="text-xs tabular-nums text-muted">{t < 60 ? `${Math.round((mb * t) / 60)} of ${mb} MB` : `${mb} MB uploaded`}</p>
        </div>
        <span className="text-xs tabular-nums text-muted">{eta}</span>
      </div>
      <div className="track"><i style={{ width: `${Math.round(p * 100)}%` }} /></div>
      <div className="flex justify-between text-sm">
        <b className="font-semibold">{done ? "Your 5 trial reels are ready" : PHASES[step]}</b>
        <span className="tabular-nums text-muted">{Math.round(p * 100)}%</span>
      </div>
      <ul className="grid gap-1.5 text-sm">
        {PHASES.map((ph, i) => {
          const state = done || i < step ? "done" : i === step ? "now" : "todo";
          return (
            <li key={ph} className={`flex items-center gap-2 ${state === "todo" ? "text-muted" : "text-ink"}`}>
              <span className={`grid h-3.5 w-3.5 place-items-center rounded-full border-[1.5px] ${state === "done" ? "border-accent bg-accent" : state === "now" ? "border-ink" : "border-[#cfcfd6]"}`} />
              {ph}
            </li>
          );
        })}
      </ul>
      <p className="min-h-[1.4em] text-sm text-soft">
        {step === 3 && <>Hook {hookIdx + 1} of 5: <b className="text-ink">&ldquo;{variants[hookIdx]?.hook}&rdquo;</b></>}
        {step === 4 && !done && <>Making variation {made + 1} of 5</>}
      </p>
      <div className="grid grid-cols-5 gap-2">
        {variants.map((v, i) => {
          const cls = done || (step === 4 && i < made) ? "on" : step === 4 || (step === 3 && i <= hookIdx) ? "busy" : "";
          return (
            <div key={v.order} className={`slot ${cls}`}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={v.cover} alt="" />
              <span className={`absolute bottom-1 left-1.5 font-mono text-[9px] ${cls === "on" ? "text-white" : "text-muted"}`}>#{i + 1}</span>
            </div>
          );
        })}
      </div>
      <p className="text-xs text-muted">You can close this tab. We&apos;ll email you when they&apos;re ready.</p>
    </div>
  );
}
