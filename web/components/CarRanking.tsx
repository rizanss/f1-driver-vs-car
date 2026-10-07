"use client";

import { useState } from "react";
import { abs, faster, sec, toSeconds } from "@/lib/format";
import { niceDomain } from "@/lib/stats";
import type { CarRating, DriverRating } from "@/lib/types";
import { Avatar } from "./Avatar";
import { useShared } from "./DataProvider";
import { RangeRows } from "./RangeRows";
import { Filters, Notes, PageHeader, SeasonNotes, Select } from "./ui";

const STEP = 0.4;

export function CarRanking({ cars, drivers }: { cars: CarRating[]; drivers: DriverRating[] }) {
  const { lap, color, teams } = useShared();
  const years = [...new Set(cars.map((c) => c.season))].sort((a, b) => b - a);
  const [season, setSeason] = useState(years[0]);

  const inSeconds = cars.map((c) => {
    const s = (v: number) => toSeconds(v, lap(c.season));
    return { ...c, value: s(c.rating), q05: s(c.q05), q95: s(c.q95) };
  });
  const domain = niceDomain(inSeconds.flatMap((c) => [c.q05, c.q95]), STEP);
  const rows = inSeconds.filter((c) => c.season === season).sort((a, b) => b.value - a.value);
  const [top, second] = rows;
  const lineup = (team: string) => drivers.filter((d) => d.season === season && d.teams.includes(team));

  return (
    <>
      <PageHeader href="/cars" title="Which car was the fastest?">
        <strong>{top.team}</strong> had the fastest car of {season}: <strong>{sec(top.value)} per lap</strong>{" "}
        against the average car, {abs(top.value - second.value)} ahead of {second.team}.
      </PageHeader>

      <Filters>
        <Select label="Season" value={season} options={years.map((y) => ({ value: y, label: String(y) }))} onChange={setSeason} />
      </Filters>

      <RangeRows
        domain={domain}
        step={STEP}
        left="Slower than average"
        right="Faster"
        rows={rows.map((c) => ({
          id: teams[c.team]?.lineage ?? c.team,
          label: (
            <div className="flex items-center gap-3">
              <span className="h-9 w-1.5 shrink-0 -skew-x-12 rounded-sm" style={{ background: color(c.team) }} />
              <div className="min-w-0">
                <div className="truncate font-display text-lg leading-tight font-bold">{c.team}</div>
                <div className="mt-0.5 flex -space-x-1.5">
                  {lineup(c.team).map((d) => (
                    <Avatar key={d.driver} code={d.driver} color={color(c.team)} size={22} className="rounded-full ring-2 ring-surface" />
                  ))}
                </div>
              </div>
            </div>
          ),
          value: c.value,
          q05: c.q05,
          q95: c.q95,
          color: color(c.team),
          tip: {
            title: `${c.team} · ${season}`,
            text: `${faster(c.value)} per lap than the average car, with the driver taken out.`,
          },
        }))}
      />

      <Notes>
        <li>
          <strong>How to read:</strong> the dot is the car&apos;s one-lap pace against the average car of {season},
          with the driver taken out. The bar is the 90% range.
        </li>
        <li>A car&apos;s pace is a season average: cars that improve or fade during the year are blended into one number.</li>
        <SeasonNotes season={season} />
      </Notes>
    </>
  );
}
