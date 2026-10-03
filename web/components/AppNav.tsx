import Link from "next/link";
import { Logo, Arrow } from "./ui";

export function AppNav({ right }: { right?: "new" | "free" }) {
  return (
    <header className="sticky top-3 z-50 px-4">
      <nav className="mx-auto flex max-w-3xl items-center justify-between rounded-full border border-line/70 bg-white/85 py-1.5 pl-5 pr-1.5 shadow-[0_8px_30px_-12px_rgba(0,0,0,.18)] backdrop-blur">
        <Logo />
        {right === "new" ? (
          <Link href="/app" className="inline-flex items-center rounded-full bg-ink py-1.5 pl-4 pr-1.5 text-sm font-medium text-white">
            New video <Arrow />
          </Link>
        ) : (
          <span className="rounded-full border border-line bg-card px-3 py-1 text-xs text-soft">1 free run</span>
        )}
      </nav>
    </header>
  );
}
