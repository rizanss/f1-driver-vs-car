"use client";

import { useState } from "react";
import { abs, faster, sec, toSeconds } from "@/lib/format";
import { niceDomain } from "@/lib/stats";
import type { DriverRating } from "@/lib/types";
import { useShared } from "./DataProvider";
import { RangeRows } from "./RangeRows";
import { DriverLabel, Filters, Notes, PageHeader, SeasonNotes, Select } from "./ui";

const STEP = 0.3;

export function DriverRanking({ drivers }: { drivers: DriverRating[] }) {
  const { lap, name, color } = useShared();
  const years = [...new Set(drivers.map((d) => d.season))].sort((a, b) => b - a);
  const [season, setSeason] = useState(years[0]);

  const inSeconds = drivers.map((d) => {
    const s = (v: number) => toSeconds(v, lap(d.season));
    return { ...d, value: s(d.rating), q05: s(d.q05), q95: s(d.q95) };
  });
  const domain = niceDomain(inSeconds.flatMap((d) => [d.q05, d.q95]), STEP);
  const rows = inSeconds.filter((d) => d.season === season).sort((a, b) => b.value - a.value);
  const [top, second] = rows;

  return (
    <>
      <PageHeader href="/" title="Who is fastest in equal machinery?">
        <strong>{name(top.driver)}</strong> was the quickest driver of {season}:{" "}
        <strong>{sec(top.value)} per lap</strong> against an average driver in the same car, and{" "}
        {abs(top.value - second.value)} clear of {name(second.driver)}.
      </PageHeader>

      <Filters>
        <Select label="Season" value={season} options={years.map((y) => ({ value: y, label: String(y) }))} onChange={setSeason} />
      </Filters>

      <RangeRows
        domain={domain}
        step={STEP}
        left="Slower than average"
        right="Faster"
        rows={rows.map((d) => ({
          id: d.driver,
          label: <DriverLabel code={d.driver} teams={d.teams} />,
          value: d.value,
          q05: d.q05,
          q95: d.q95,
          color: color(d.teams[d.teams.length - 1]),
          tip: {
            title: `${name(d.driver)} · ${season}`,
            text: `${faster(d.value)} per lap than an average driver in the same car.`,
          },
        }))}
      />

      <Notes>
        <li>
          <strong>How to read:</strong> the dot is the best estimate of one-lap pace against an average driver in
          the same car. The bar is the 90% range: a short bar means the model is sure, a long one means it is not.
        </li>
        <li>
          Seconds assume the typical pole lap of {season} ({lap(season).toFixed(1)} s). Wet sessions are left out.
        </li>
        <SeasonNotes season={season} />
      </Notes>
    </>
  );
}
