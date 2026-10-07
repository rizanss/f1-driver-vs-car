"use client";

import { useMemo, useState } from "react";
import { abs, faster, pct, span, toSeconds } from "@/lib/format";
import { autoStep, mean, niceDomain, share, summarize } from "@/lib/stats";
import type { CarDraws, DriverDraws, DriverRating } from "@/lib/types";
import { Avatar } from "./Avatar";
import { useShared } from "./DataProvider";
import { RangeRows } from "./RangeRows";
import { DriverLabel, Filters, Notes, PageHeader, SeasonNotes, Select } from "./ui";

type Choice = { season: number; driver: string; team: string };
type Draws = { drivers: DriverDraws[]; cars: CarDraws[] };

const byKey = <T extends { season: number; draws: number[] }>(list: T[], key: (x: T) => string) =>
  Object.fromEntries(list.map((x) => [`${key(x)} ${x.season}`, x.draws]));

export function Swap({ drivers, draws }: { drivers: DriverRating[]; draws: Draws }) {
  const { lap, color, name } = useShared();
  const D = useMemo(() => byKey(draws.drivers, (d) => d.driver), [draws]);
  const C = useMemo(() => byKey(draws.cars, (c) => c.team), [draws]);
  const years = [...new Set(drivers.map((d) => d.season))].sort((a, b) => b - a);

  const lineupOf = (season: number) => drivers.filter((d) => d.season === season);
  const carsOf = (season: number) =>
    draws.cars.filter((c) => c.season === season).sort((a, b) => mean(b.draws) - mean(a.draws));

  const defaults = (season: number): Choice => {
    const team = carsOf(season)[0].team;
    const driver = lineupOf(season)
      .filter((d) => !d.teams.includes(team))
      .sort((a, b) => b.rating - a.rating)[0].driver;
    return { season, driver, team };
  };
  const [choice, setChoice] = useState(() => defaults(years[0]));
  const { season, driver, team } = choice;

  const score = (d: string, t: string) => D[`${d} ${season}`].map((x, i) => x + C[`${t} ${season}`][i]);
  const pairs = lineupOf(season).flatMap((d) => d.teams.map((t) => ({ driver: d.driver, team: t, score: score(d.driver, t) })));
  const pole = pairs[0].score.map((_, i) => Math.max(...pairs.map((p) => p.score[i])));
  const gap = (s: number[]) => s.map((x, i) => toSeconds(pole[i] - x, lap(season)));

  const isReal = pairs.some((p) => p.driver === driver && p.team === team);
  const swapGap = gap(score(driver, team));
  const rows = [
    ...pairs.map((p) => ({ ...p, id: `${p.driver}-${p.team}`, gap: gap(p.score), highlight: p.driver === driver && p.team === team })),
    ...(isReal ? [] : [{ driver, team, id: "swap", gap: swapGap, highlight: true }]),
  ]
    .map((r) => ({ ...r, ...summarize(r.gap) }))
    .sort((a, b) => a.value - b.value);
  const result = rows.find((r) => r.highlight)!;
  const position = rows.indexOf(result) + 1;
  const bounds = rows.flatMap((r) => [r.q05, r.q95]);
  const step = autoStep(bounds);
  const domain = niceDomain(bounds, step);
  const onPole = result.value < 0;

  return (
    <>
      <PageHeader href="/swap" title="What if they swapped cars?">
        <strong>{name(driver)}</strong> in the {season} {team} would be{" "}
        <strong>{onPole ? `on pole by ${abs(result.value)}` : `${abs(result.value)} off pole`}</strong>, around P
        {position} on that grid.
      </PageHeader>

      <Filters>
        <Select
          label="Season"
          value={season}
          options={years.map((y) => ({ value: y, label: String(y) }))}
          onChange={(y) => setChoice(defaults(y))}
        />
        <Select
          label="Driver"
          value={driver}
          options={lineupOf(season)
            .map((d) => d.driver)
            .sort()
            .map((d) => ({ value: d, label: `${d} · ${name(d)}` }))}
          onChange={(d) => setChoice({ ...choice, driver: d })}
        />
        <Select
          label="Car"
          value={team}
          options={carsOf(season).map((c) => ({ value: c.team, label: c.team }))}
          onChange={(t) => setChoice({ ...choice, team: t })}
        />
      </Filters>

      <div className="card mb-4 flex flex-col gap-6 overflow-hidden p-5 sm:flex-row sm:items-center sm:p-6">
        <Avatar key={`${driver}-${team}`} code={driver} color={color(team)} size={168} className="animate-fade-in rounded-2xl" />
        <div>
          <p className="kicker text-xs">
            {driver} · {season} {team}
          </p>
          <p className="mt-2 text-6xl font-semibold">
            {abs(result.value)}{" "}
            <span className="text-2xl font-medium text-ink-2">{onPole ? "faster than pole" : "off pole"}</span>
          </p>
          <dl className="mt-4 flex flex-wrap gap-x-8 gap-y-2 text-sm">
            <div>
              <dt className="text-muted">Grid slot</dt>
              <dd className="text-lg font-semibold">P{position}</dd>
            </div>
            <div>
              <dt className="text-muted">Pole in</dt>
              <dd className="text-lg font-semibold">{pct(share(swapGap, (g) => g < 0))} of simulations</dd>
            </div>
            <div>
              <dt className="text-muted">Gap to pole, 90%</dt>
              <dd className="text-lg font-semibold">{span(result.q05, result.q95)}</dd>
            </div>
          </dl>
        </div>
      </div>

      <RangeRows
        domain={domain}
        step={step}
        left="Closer to pole"
        right="Further off"
        rows={rows.map((r) => ({
          id: r.id,
          label: <DriverLabel code={r.driver} teams={[r.team]} detail={r.id === "swap" ? `Swap · ${r.team}` : r.team} />,
          value: r.value,
          q05: r.q05,
          q95: r.q95,
          color: color(r.team),
          highlight: r.highlight,
          tip: {
            title: r.id === "swap" ? `${name(r.driver)} in the ${season} ${r.team}` : `${name(r.driver)} · ${r.team}`,
            text:
              Math.round(r.value * 100) === 0
                ? "Level with pole on a typical lap."
                : `${faster(-r.value)} than pole on a typical ${season} lap.`,
            note: r.q05 < 0 ? "minus is ahead of pole" : undefined,
          },
        }))}
      />

      <Notes>
        <li>
          <strong>A what-if, not a prediction:</strong> driver pace plus car pace, averaged over the season&apos;s
          tracks. The gap is to the fastest real driver–car pairing of {season}, on a typical pole lap of{" "}
          {lap(season).toFixed(1)} s.
        </li>
        <li>Drivers who changed teams mid-season appear once per car.</li>
        <SeasonNotes season={season} />
      </Notes>
    </>
  );
}
