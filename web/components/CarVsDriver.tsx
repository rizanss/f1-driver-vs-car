"use client";

import { pct } from "@/lib/format";
import type { EraInfo, SeasonInfo } from "@/lib/types";
import { Notes, PageHeader } from "./ui";

const label = (era: string) => era.replace("-", "–");
const rest = (share: number) => `${100 - Math.round(share * 100)}%`;

function Split({ share, q05, q95, thick = false }: { share: number; q05: number; q95: number; thick?: boolean }) {
  return (
    <div className={`relative flex gap-0.5 ${thick ? "h-4" : "h-3"}`}>
      <span className="rounded-l-sm bg-car transition-all duration-700" style={{ width: `${share * 100}%` }} />
      <span className="flex-1 rounded-r-sm bg-driver" />
      <span
        className="absolute -inset-y-1 border-x border-ink/80"
        style={{ left: `${q05 * 100}%`, width: `${(q95 - q05) * 100}%` }}
      />
    </div>
  );
}

export function CarVsDriver({ seasons, eras }: { seasons: SeasonInfo[]; eras: EraInfo[] }) {
  const [now, before] = [eras[eras.length - 1], eras[eras.length - 2]];

  return (
    <>
      <PageHeader href="/car-vs-driver" title="Is it the car or the driver?">
        In {label(now.era)} the car decides <strong>{pct(now.car_share)}</strong> of the gaps on the qualifying
        sheet. In {label(before.era)} it was <strong>{pct(before.car_share)}</strong>, leaving{" "}
        {rest(before.car_share)} to the drivers.
      </PageHeader>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 pb-4 text-sm text-ink-2">
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-4 rounded-sm bg-car" /> Car
        </span>
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-4 rounded-sm bg-driver" /> Driver
        </span>
        <span className="flex items-center gap-2">
          <span className="h-3 w-3 border-x border-ink/80" /> 90% range
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {eras.map((e, i) => (
          <div key={e.era} className="card animate-rise p-5" style={{ animationDelay: `${i * 90}ms` }}>
            <p className="kicker text-xs">{label(e.era)}</p>
            <p className="mt-2 text-5xl font-semibold">
              {pct(e.car_share)} <span className="text-lg font-medium text-ink-2">car</span>
            </p>
            <div className="mt-4">
              <Split share={e.car_share} q05={e.q05} q95={e.q95} thick />
            </div>
            <p className="mt-3 text-sm text-muted">
              {rest(e.car_share)} driver · 90% range {pct(e.q05)}–{pct(e.q95)} car
            </p>
          </div>
        ))}
      </div>

      <div className="card mt-4 p-4 sm:p-6">
        <p className="kicker mb-4 text-xs">Season by season</p>
        <ol className="space-y-3">
          {seasons.map((s, i) => (
            <li
              key={s.season}
              className="grid animate-fade-in grid-cols-[3rem_minmax(0,1fr)_5.5rem] items-center gap-4 sm:grid-cols-[3.5rem_minmax(0,1fr)_8rem]"
              style={{ animationDelay: `${200 + i * 50}ms` }}
            >
              <span className="font-display text-lg font-bold">{s.season}</span>
              <Split share={s.car_share} q05={s.q05} q95={s.q95} />
              <span className="text-right text-sm leading-tight tabular-nums">
                <span className="font-semibold">{pct(s.car_share)} car</span>
                <span className="block text-xs text-muted">
                  {pct(s.q05)}–{pct(s.q95)}
                </span>
              </span>
            </li>
          ))}
        </ol>
      </div>

      <Notes>
        <li>
          <strong>How it is measured:</strong> how much the cars differ from each other, against how much the drivers
          differ, within one season. If every car were equal, the car share would be 0%.
        </li>
        <li>
          The share covers the whole grid, not just the front: one dominant car barely moves it when the rest of the
          field is close.
        </li>
      </Notes>
    </>
  );
}
