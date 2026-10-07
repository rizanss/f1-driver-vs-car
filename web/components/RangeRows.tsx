import { sec, signed, span } from "@/lib/format";
import { ticks } from "@/lib/stats";

export type RangeRow = {
  id: string;
  label: React.ReactNode;
  value: number;
  q05: number;
  q95: number;
  color: string;
  tip: { title: string; text: string; note?: string };
  highlight?: boolean;
};

const COLS = "grid grid-cols-[1.25rem_minmax(0,1fr)_auto] gap-x-3 sm:grid-cols-[2rem_15rem_minmax(0,1fr)_6.5rem] sm:gap-x-4";

export function RangeRows({
  rows,
  domain,
  step,
  left,
  right,
}: {
  rows: RangeRow[];
  domain: [number, number];
  step: number;
  left: string;
  right: string;
}) {
  const x = (v: number) => ((v - domain[0]) / (domain[1] - domain[0])) * 100;
  const marks = ticks(domain, step);

  return (
    <div className="card overflow-hidden [--row:5.5rem] sm:[--row:3.75rem]">
      <div className={`${COLS} items-end border-b border-grid px-3 pt-4 pb-2 text-xs text-muted sm:px-5`}>
        <span className="hidden sm:block" />
        <span className="hidden sm:block" />
        <div className="relative col-span-3 h-9 sm:col-span-1">
          <span className="absolute top-0 left-0">← {left}</span>
          <span className="absolute top-0 right-0">{right} →</span>
          {marks.map((t, i) => (
            <span
              key={t}
              className={`absolute bottom-0 tabular-nums ${i === 0 ? "" : i === marks.length - 1 ? "-translate-x-full" : "-translate-x-1/2"}`}
              style={{ left: `${x(t)}%` }}
            >
              {signed(t, 1)}
            </span>
          ))}
        </div>
        <span className="hidden text-right sm:block">Per lap</span>
      </div>

      <ol className="relative" style={{ height: `calc(var(--row) * ${rows.length})` }}>
        {rows.map((r, i) => (
          <li
            key={r.id}
            className={`${COLS} absolute inset-x-0 animate-fade-in content-center items-center gap-y-2 border-b border-grid/70 px-3 transition-transform duration-700 ease-[cubic-bezier(0.2,0.8,0.2,1)] focus-within:z-20 hover:z-20 hover:bg-raised/50 sm:px-5 ${
              r.highlight ? "bg-accent/10 shadow-[inset_3px_0_0_var(--color-accent)]" : ""
            }`}
            style={{ height: "var(--row)", transform: `translateY(calc(var(--row) * ${i}))` }}
          >
            <span className="font-display text-lg font-bold text-muted tabular-nums">{i + 1}</span>
            <div className="min-w-0">{r.label}</div>
            <div className="text-right leading-tight tabular-nums sm:col-start-4 sm:row-start-1">
              <div className="font-semibold">{sec(r.value)}</div>
              <div className="text-xs text-muted">
                {signed(r.q05)} to {signed(r.q95)}
              </div>
            </div>
            <div
              tabIndex={0}
              className="group/plot relative col-span-3 h-4 outline-none sm:col-span-1 sm:col-start-3 sm:row-start-1 sm:h-full"
            >
              {marks.map((t) => (
                <span
                  key={t}
                  className={`absolute inset-y-0 w-px ${t === 0 ? "bg-axis" : "bg-grid"}`}
                  style={{ left: `${x(t)}%` }}
                />
              ))}
              <span
                className="absolute top-1/2 h-2.5 -translate-y-1/2 rounded-full transition-all duration-700"
                style={{
                  left: `${x(r.q05)}%`,
                  width: `${x(r.q95) - x(r.q05)}%`,
                  background: `color-mix(in srgb, ${r.color} 45%, transparent)`,
                }}
              />
              <span
                className="absolute top-1/2 size-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-surface transition-all duration-700"
                style={{ left: `${x(r.value)}%`, background: r.color }}
              />
              <div
                role="tooltip"
                className={`pointer-events-none absolute z-10 w-64 rounded-xl border border-axis bg-raised px-3 py-2 text-left text-sm leading-snug opacity-0 shadow-xl shadow-black/60 transition-opacity group-hover/plot:opacity-100 group-focus/plot:opacity-100 ${
                  i === 0 ? "top-[calc(50%+14px)]" : "bottom-[calc(50%+14px)]"
                } ${x(r.value) > 60 ? "-translate-x-[calc(100%-1rem)]" : x(r.value) < 40 ? "-translate-x-4" : "-translate-x-1/2"}`}
                style={{ left: `${x(r.value)}%` }}
              >
                <div className="font-semibold">{r.tip.title}</div>
                <div className="text-ink-2">{r.tip.text}</div>
                <div className="mt-1 text-xs text-muted">
                  90% range {span(r.q05, r.q95)}
                  {r.tip.note && ` · ${r.tip.note}`}
                </div>
                <div className="text-xs text-muted">Dot: best estimate · Bar: 90% range</div>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
