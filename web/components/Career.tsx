"use client";

import { useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";
import { sec, signed, span, toSeconds } from "@/lib/format";
import { niceDomain, ticks } from "@/lib/stats";
import { AXIS_TICK, THEME } from "@/lib/theme";
import type { DriverRating } from "@/lib/types";
import { Avatar } from "./Avatar";
import { useShared } from "./DataProvider";
import { Filters, Notes, PageHeader, Select } from "./ui";

const STEP = 0.3;

type Point = { season: number; value?: number; range?: [number, number]; teams?: string[] };

function CareerTip({ active, payload }: TooltipContentProps) {
  const p = payload?.[0]?.payload as Point | undefined;
  if (!active || p?.value === undefined) return null;
  return (
    <div className="card px-3 py-2 text-sm shadow-xl shadow-black/50">
      <div className="text-base font-semibold tabular-nums">{sec(p.value)}</div>
      <div className="text-xs text-ink-2">
        {p.season} · {p.teams!.join(" → ")}
      </div>
      <div className="text-xs text-muted">90% range {span(...p.range!)}</div>
    </div>
  );
}

export function Career({ drivers }: { drivers: DriverRating[] }) {
  const { lap, color, name } = useShared();
  const seasons = [...new Set(drivers.map((d) => d.season))].sort();
  const codes = [...new Set(drivers.map((d) => d.driver))].sort();
  const [code, setCode] = useState(codes.includes("HAM") ? "HAM" : codes[0]);

  const inSeconds = drivers.map((d) => {
    const s = (v: number) => toSeconds(v, lap(d.season));
    return { ...d, value: s(d.rating), q05: s(d.q05), q95: s(d.q95) };
  });
  const domain = niceDomain(inSeconds.flatMap((d) => [d.q05, d.q95]), STEP);
  const career = inSeconds.filter((d) => d.driver === code);
  const data: Point[] = seasons.map((season) => {
    const d = career.find((c) => c.season === season);
    return d ? { season, value: d.value, range: [d.q05, d.q95], teams: d.teams } : { season };
  });
  const best = career.reduce((a, b) => (b.value > a.value ? b : a));
  const teams = [...new Set(career.flatMap((d) => d.teams))];
  const latest = career[career.length - 1];

  return (
    <>
      <PageHeader href="/career" title="How did a driver evolve?">
        <strong>{name(code)}</strong> was at their fastest in {best.season}:{" "}
        <strong>{sec(best.value)} per lap</strong> against an average driver in the same car.
      </PageHeader>

      <Filters>
        <Select
          label="Driver"
          value={code}
          options={codes.map((c) => ({ value: c, label: `${c} · ${name(c)}` }))}
          onChange={setCode}
        />
      </Filters>

      <div className="card animate-fade-in p-4 sm:p-6" key={code}>
        <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Avatar code={code} color={color(latest.teams[latest.teams.length - 1])} size={64} />
            <div>
              <div className="font-display text-2xl leading-tight font-bold uppercase">{name(code)}</div>
              <div className="text-sm text-muted">
                {career.length} {career.length === 1 ? "season" : "seasons"} · {career[0].season}–{latest.season}
              </div>
            </div>
          </div>
          <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-2">
            {teams.map((t) => (
              <li key={t} className="flex items-center gap-2">
                <span className="size-2.5 rounded-full" style={{ background: color(t) }} />
                {t}
              </li>
            ))}
          </ul>
        </div>

        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke={THEME.grid} />
            <XAxis dataKey="season" tick={AXIS_TICK} stroke={THEME.axis} tickLine={false} />
            <YAxis
              domain={domain}
              ticks={ticks(domain, STEP)}
              tickFormatter={(v: number) => `${signed(v, 1)} s`}
              tick={AXIS_TICK}
              axisLine={false}
              tickLine={false}
              width={52}
            />
            <ReferenceLine y={0} stroke={THEME.muted} strokeOpacity={0.6} />
            <Tooltip content={CareerTip} cursor={{ stroke: THEME.axis }} />
            <Area dataKey="range" stroke="none" fill={THEME.ink2} fillOpacity={0.1} activeDot={false} />
            <Line
              dataKey="value"
              stroke={THEME.ink2}
              strokeWidth={2}
              activeDot={false}
              dot={({ cx, cy, payload }: { cx?: number; cy?: number; payload: Point }) => (
                <circle
                  key={payload.season}
                  cx={cx}
                  cy={cy}
                  r={payload.value === undefined ? 0 : 6}
                  fill={payload.teams ? color(payload.teams[payload.teams.length - 1]) : "none"}
                  stroke={THEME.surface}
                  strokeWidth={2}
                />
              )}
            />
          </ComposedChart>
        </ResponsiveContainer>

        <table className="mt-6 w-full text-sm">
          <thead className="border-b border-grid text-left text-xs text-muted">
            <tr>
              <th className="py-2 font-medium">Season</th>
              <th className="py-2 font-medium">Team</th>
              <th className="py-2 text-right font-medium">Pace vs average</th>
              <th className="hidden py-2 text-right font-medium sm:table-cell">90% range</th>
            </tr>
          </thead>
          <tbody className="tabular-nums">
            {career.map((d) => (
              <tr key={d.season} className="border-b border-grid/60">
                <td className="py-2">{d.season}</td>
                <td className="py-2 text-ink-2">{d.teams.join(" → ")}</td>
                <td className="py-2 text-right font-semibold">{sec(d.value)}</td>
                <td className="hidden py-2 text-right text-muted sm:table-cell">{span(d.q05, d.q95)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Notes>
        <li>
          <strong>How to read:</strong> each dot is one season, coloured by team. The shaded band is the 90% range.
          Above zero means faster than an average driver in the same car.
        </li>
        <li>Each season is measured against that season&apos;s grid, so a flat line means the driver kept pace with the field.</li>
      </Notes>
    </>
  );
}
