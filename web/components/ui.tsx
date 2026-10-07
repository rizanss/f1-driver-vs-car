"use client";

import { FEATURES } from "@/lib/features";
import { Avatar } from "./Avatar";
import { useShared } from "./DataProvider";

export const CURRENT_SEASON = 2026;

export function PageHeader({
  href,
  title,
  children,
}: {
  href: (typeof FEATURES)[number]["href"];
  title: string;
  children?: React.ReactNode;
}) {
  const i = FEATURES.findIndex((f) => f.href === href);
  return (
    <div className="animate-rise pt-10 pb-7 sm:pt-14">
      <p className="kicker">
        <span className="text-accent">{String(i + 1).padStart(2, "0")}</span> / {FEATURES[i].label}
      </p>
      <h1 className="mt-3 max-w-3xl font-display text-4xl leading-[0.95] font-bold tracking-tight uppercase sm:text-6xl">
        {title}
      </h1>
      {children && (
        <p className="mt-4 max-w-2xl text-lg text-ink-2 [&_strong]:font-semibold [&_strong]:text-ink">{children}</p>
      )}
    </div>
  );
}

export function Filters({ children }: { children: React.ReactNode }) {
  return <div className="mb-4 flex flex-wrap items-end gap-3">{children}</div>;
}

export function Select<T extends string | number>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="kicker text-xs">{label}</span>
      <select
        className="select"
        value={String(value)}
        onChange={(e) => onChange(options.find((o) => String(o.value) === e.target.value)!.value)}
      >
        {options.map((o) => (
          <option key={String(o.value)} value={String(o.value)}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function Notes({ children }: { children: React.ReactNode }) {
  return <ul className="mt-5 space-y-1.5 text-sm text-muted [&_strong]:font-semibold [&_strong]:text-ink-2">{children}</ul>;
}

export function SeasonNotes({ season }: { season: number }) {
  const { seasons } = useShared();
  return (
    <>
      {season === CURRENT_SEASON && (
        <li>
          <strong>{season} is still running:</strong> based on the first {seasons[season].rounds} rounds.
        </li>
      )}
      {season <= 2020 && (
        <li>
          <strong>Haas 2018–2020:</strong> MAG and GRO only ever drove for Haas in this data, so the split
          between their pace and the car&apos;s is less certain.
        </li>
      )}
    </>
  );
}

export function DriverLabel({ code, teams, detail }: { code: string; teams: string[]; detail?: string }) {
  const { name, color } = useShared();
  return (
    <div className="flex items-center gap-3">
      <Avatar code={code} color={color(teams[teams.length - 1])} size={40} />
      <div className="min-w-0 leading-tight">
        <div className="flex items-baseline gap-2">
          <span className="font-display text-lg font-bold">{code}</span>
          <span className="hidden truncate text-sm text-ink-2 sm:inline">{name(code)}</span>
        </div>
        <div className="truncate text-xs text-muted">{detail ?? teams.join(" → ")}</div>
      </div>
    </div>
  );
}
