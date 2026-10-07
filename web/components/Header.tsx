"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { FEATURES } from "@/lib/features";

export function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const menu = useRef<HTMLDivElement>(null);
  const current = FEATURES.find((f) => f.href === pathname) ?? FEATURES[0];

  useEffect(() => {
    if (!open) return;
    const onPointer = (e: PointerEvent) => {
      if (!menu.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <header className="sticky top-0 z-30 border-b border-grid bg-page/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-3">
          <span className="flex gap-1" aria-hidden>
            <span className="h-5 w-1.5 -skew-x-12 bg-accent" />
            <span className="h-5 w-1.5 -skew-x-12 bg-accent/60" />
          </span>
          <span className="font-display text-xl font-bold tracking-wide uppercase italic">
            Driver <span className="text-muted">vs</span> Car
          </span>
          <span className="hidden text-sm text-muted md:inline">F1 qualifying · 2018–2026</span>
        </Link>

        <div ref={menu} className="relative">
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            aria-haspopup="true"
            className="flex items-center gap-3 rounded-lg border border-axis bg-surface px-3 py-2 text-sm transition-colors hover:border-muted"
          >
            <span className="kicker hidden text-xs sm:inline">Features</span>
            <span className="font-semibold">{current.label}</span>
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              aria-hidden
              className={`transition-transform ${open ? "rotate-180" : ""}`}
            >
              <path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.6" />
            </svg>
          </button>

          {open && (
            <nav className="card absolute right-0 mt-2 w-80 animate-fade-in overflow-hidden p-1.5 shadow-2xl shadow-black/60">
              {FEATURES.map((f, i) => {
                const active = f.href === current.href;
                return (
                  <Link
                    key={f.href}
                    href={f.href}
                    onClick={() => setOpen(false)}
                    aria-current={active ? "page" : undefined}
                    className={`flex items-start gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-raised ${active ? "bg-raised" : ""}`}
                  >
                    <span className={`font-display text-sm font-bold ${active ? "text-accent" : "text-muted"}`}>
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span>
                      <span className="block font-semibold">{f.label}</span>
                      <span className="block text-sm text-muted">{f.blurb}</span>
                    </span>
                  </Link>
                );
              })}
            </nav>
          )}
        </div>
      </div>
    </header>
  );
}
