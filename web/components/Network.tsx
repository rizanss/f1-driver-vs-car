"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { years } from "@/lib/format";
import type { Network as NetworkData } from "@/lib/types";
import { Avatar } from "./Avatar";
import { useShared } from "./DataProvider";
import { Filters, Notes, PageHeader, Select } from "./ui";

const NetworkGraph = dynamic(() => import("./NetworkGraph").then((m) => m.NetworkGraph), {
  ssr: false,
  loading: () => <div className="h-[420px]" />,
});

export function Network({ network }: { network: NetworkData }) {
  const { people, name } = useShared();
  const [selected, setSelected] = useState<string | null>(null);
  const team = network.teams.find((t) => t.id === selected);
  const teamColor = (id: string) => network.teams.find((t) => t.id === id)!.color;
  const stints = network.links
    .filter((l) => l.source === selected || l.target === selected)
    .sort((a, b) => a.seasons[0] - b.seasons[0]);
  const movers = network.drivers.filter((d) => network.links.filter((l) => l.source === d.id).length > 1);
  const codes = network.drivers.map((d) => d.id).sort();

  return (
    <>
      <PageHeader href="/network" title="Who drove for whom?">
        <strong>
          {movers.length} of {network.drivers.length} drivers
        </strong>{" "}
        raced for two or more teams. They link every team together, and that is what lets the model compare drivers
        in different cars.
      </PageHeader>

      <Filters>
        <Select
          label="Find a driver"
          value={team ? "" : (selected ?? "")}
          options={[{ value: "", label: "Everyone" }, ...codes.map((c) => ({ value: c, label: `${c} · ${name(c)}` }))]}
          onChange={(v) => setSelected(v || null)}
        />
      </Filters>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_18rem]">
        <div className="card overflow-hidden">
          <NetworkGraph network={network} people={people} selected={selected} onSelect={setSelected} />
        </div>

        <aside className="card p-5">
          {!selected && (
            <div className="space-y-3 text-sm text-ink-2">
              <p className="font-semibold text-ink">Click a driver or a team.</p>
              <p>Big circle: a team. Small photo: a driver. A ring marks a driver who raced for two or more teams.</p>
              <p>Thicker lines mean more seasons together.</p>
            </div>
          )}

          {team && (
            <div className="animate-fade-in">
              <span className="block h-1.5 w-12 -skew-x-12" style={{ background: team.color }} />
              <h2 className="mt-3 font-display text-2xl font-bold uppercase">{team.id}</h2>
              {team.names.length > 1 && (
                <p className="text-sm text-muted">Also: {team.names.filter((n) => n !== team.id).join(", ")}</p>
              )}
              <ul className="mt-4 space-y-2">
                {stints.map((s) => (
                  <li key={s.source} className="flex items-center gap-3">
                    <Avatar code={s.source} color={team.color} size={32} />
                    <span className="min-w-0 flex-1 truncate font-semibold">{name(s.source)}</span>
                    <span className="text-sm text-muted tabular-nums">{years(s.seasons)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {selected && !team && (
            <div className="animate-fade-in" key={selected}>
              <Avatar code={selected} color={teamColor(stints[stints.length - 1].target)} size={88} className="rounded-2xl" />
              <h2 className="mt-3 font-display text-2xl leading-tight font-bold uppercase">{name(selected)}</h2>
              <ul className="mt-4 space-y-2">
                {stints.map((s) => (
                  <li key={s.target} className="flex items-center gap-3">
                    <span className="h-5 w-1.5 shrink-0 -skew-x-12" style={{ background: teamColor(s.target) }} />
                    <span className="min-w-0 flex-1 truncate font-semibold">{s.target}</span>
                    <span className="text-sm text-muted tabular-nums">{years(s.seasons)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>
      </div>

      <Notes>
        <li>
          <strong>Renamed teams count as one:</strong> Toro Rosso, AlphaTauri, RB and Racing Bulls are the same team,
          and so are Force India, Racing Point and Aston Martin.
        </li>
        <li>Drag the circles to pull the network apart.</li>
      </Notes>
    </>
  );
}
