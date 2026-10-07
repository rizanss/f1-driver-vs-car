"use client";

import { useMemo, useState } from "react";
import { abs, pct, span, toSeconds } from "@/lib/format";
import { share, summarize } from "@/lib/stats";
import { THEME } from "@/lib/theme";
import type { DriverDraws, DriverRating } from "@/lib/types";
import { Avatar } from "./Avatar";
import { useShared } from "./DataProvider";
import { Notes, PageHeader, Select } from "./ui";

const BINS = 30;

type Pick = { driver: string; season: number };

function histogram(xs: number[]) {
  const edge = Math.max(...xs.map(Math.abs)) || 1;
  const width = (2 * edge) / BINS;
  const counts = Array.from({ length: BINS }, () => 0);
  xs.forEach((x) => counts[Math.min(BINS - 1, Math.floor((x + edge) / width))]++);
  return counts.map((n, i) => ({ n, mid: -edge + (i + 0.5) * width }));
}

export function HeadToHead({ drivers, draws }: { drivers: DriverRating[]; draws: DriverDraws[] }) {
  const { lap, color, name } = useShared();
  const D = useMemo(() => Object.fromEntries(draws.map((d) => [`${d.driver} ${d.season}`, d.draws])), [draws]);
  const codes = [...new Set(drivers.map((d) => d.driver))].sort();
  const seasonsOf = (code: string) => drivers.filter((d) => d.driver === code).map((d) => d.season).sort((a, b) => b - a);
  const teamOf = ({ driver, season }: Pick) => {
    const teams = drivers.find((d) => d.driver === driver && d.season === season)!.teams;
    return teams[teams.length - 1];
  };

  const [a, setA] = useState<Pick>({ driver: "VER", season: 2021 });
  const [b, setB] = useState<Pick>({ driver: "HAM", season: 2021 });
  const seconds = (p: Pick) => D[`${p.driver} ${p.season}`].map((x) => toSeconds(x, lap(p.season)));
  const sb = seconds(b);
  const diff = seconds(a).map((x, i) => x - sb[i]);
  const chance = share(diff, (d) => d > 0);
  const gap = summarize(diff);
  const same = a.driver === b.driver && a.season === b.season;
  const colorA = color(teamOf(a));
  const colorB = teamOf(a) === teamOf(b) ? THEME.ink2 : color(teamOf(b));
  const bins = histogram(diff);
  const peak = Math.max(...bins.map((x) => x.n));
  const [winner, loser] = gap.value >= 0 ? [a, b] : [b, a];

  const side = (pick: Pick, set: (p: Pick) => void, accent: string, align: "left" | "right") => (
    <div className={`flex flex-col gap-4 ${align === "right" ? "sm:items-end sm:text-right" : ""}`}>
      <Avatar key={`${pick.driver}-${pick.season}`} code={pick.driver} color={color(teamOf(pick))} size={176} className="animate-fade-in rounded-2xl" />
      <div>
        <div className="font-display text-3xl leading-none font-bold uppercase">{name(pick.driver)}</div>
        <div className={`mt-1 flex items-center gap-2 text-sm text-ink-2 ${align === "right" ? "sm:justify-end" : ""}`}>
          <span className="size-2.5 rounded-full" style={{ background: accent }} />
          {pick.season} · {teamOf(pick)}
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <Select
          label="Driver"
          value={pick.driver}
          options={codes.map((c) => ({ value: c, label: `${c} · ${name(c)}` }))}
          onChange={(driver) => {
            const seasons = seasonsOf(driver);
            set({ driver, season: seasons.includes(pick.season) ? pick.season : seasons[0] });
          }}
        />
        <Select
          label="Season"
          value={pick.season}
          options={seasonsOf(pick.driver).map((s) => ({ value: s, label: String(s) }))}
          onChange={(season) => set({ ...pick, season })}
        />
      </div>
    </div>
  );

  return (
    <>
      <PageHeader href="/head-to-head" title="Who is faster, and how sure?">
        {same ? (
          "Pick two different drivers or seasons."
        ) : (
          <>
            In equal cars, <strong>{name(a.driver)}</strong> ({a.season}) beats <strong>{name(b.driver)}</strong> (
            {b.season}) in <strong>{pct(chance)}</strong> of the model&apos;s simulations.
          </>
        )}
      </PageHeader>

      <div className="card grid gap-8 p-5 sm:grid-cols-[1fr_auto_1fr] sm:items-center sm:p-8">
        {side(a, setA, colorA, "left")}

        <div className="text-center">
          <div className="text-7xl font-semibold">{pct(chance)}</div>
          <div className="mt-1 text-sm text-ink-2">chance {a.driver} is faster</div>
          <div className="mx-auto mt-4 flex h-3 w-48 gap-0.5">
            <span className="rounded-l-sm transition-all duration-700" style={{ width: `${chance * 100}%`, background: colorA }} />
            <span className="flex-1 rounded-r-sm" style={{ background: colorB }} />
          </div>
        </div>

        {side(b, setB, colorB, "right")}
      </div>

      {!same && (
        <div className="card mt-4 p-5 sm:p-6">
          <p className="text-ink-2">
            Expected gap in equal cars: <strong className="text-ink">{abs(gap.value)} per lap</strong> to{" "}
            {winner.driver} over {loser.driver}. 90% range {span(gap.q05, gap.q95)}.
          </p>
          <div className="relative mt-5 flex h-32 items-end gap-0.5" role="img" aria-label="Distribution of the simulated gap">
            <span className="absolute inset-y-0 left-1/2 w-px bg-muted/60" />
            {bins.map((x) => (
              <span
                key={x.mid}
                title={`${x.n} simulations`}
                className="flex-1 rounded-t-sm transition-all duration-500"
                style={{ height: `${(x.n / peak) * 100}%`, background: x.mid > 0 ? colorA : colorB }}
              />
            ))}
          </div>
          <div className="mt-2 flex justify-between border-t border-axis pt-2 text-xs text-muted">
            <span>← {b.driver} faster</span>
            <span>Equal</span>
            <span>{a.driver} faster →</span>
          </div>
        </div>
      )}

      <Notes>
        <li>
          <strong>How to read:</strong> the model draws 400 plausible versions of both drivers&apos; pace. The chance is
          the share of draws where {a.driver} comes out ahead; the bars show how those draws spread.
        </li>
        {a.season !== b.season && (
          <li>
            <strong>Different seasons:</strong> each rating is measured against its own season&apos;s grid, so this
            compares how far each driver stood above their field.
          </li>
        )}
      </Notes>
    </>
  );
}
