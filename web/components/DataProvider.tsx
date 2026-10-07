"use client";

import { createContext, useContext } from "react";
import type { Shared } from "@/lib/types";

const SharedContext = createContext<Shared | null>(null);

export function DataProvider({ value, children }: { value: Shared; children: React.ReactNode }) {
  return <SharedContext value={value}>{children}</SharedContext>;
}

export function useShared() {
  const value = useContext(SharedContext);
  if (!value) throw new Error("useShared must be used inside DataProvider");
  const color = (team: string) => value.teams[team]?.color ?? "#898781";
  const lap = (season: number) => value.seasons[season].pole_lap;
  const name = (code: string) => value.people[code]?.name ?? code;
  return { ...value, color, lap, name };
}
