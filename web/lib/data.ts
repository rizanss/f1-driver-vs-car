import { readFileSync } from "node:fs";
import path from "node:path";
import type { CarDraws, CarRating, DriverDraws, DriverRating, EraInfo, Network, Person, SeasonInfo, Shared } from "./types";

const OUTPUTS = path.join(process.cwd(), "..", "outputs");

function read<T>(file: string): T {
  return JSON.parse(readFileSync(path.join(OUTPUTS, file), "utf8"));
}

export const getRatings = () => read<{ drivers: DriverRating[]; cars: CarRating[] }>("ratings.json");
export const getSeasons = () => read<{ seasons: SeasonInfo[]; eras: EraInfo[] }>("seasons.json");
export const getDraws = () => read<{ drivers: DriverDraws[]; cars: CarDraws[] }>("draws.json");
export const getNetwork = () => read<Network>("network.json");

export function getShared(): Shared {
  const teams = getNetwork().teams.flatMap((t) => t.names.map((name) => [name, { lineage: t.id, color: t.color }]));
  return {
    people: read<Record<string, Person>>("drivers.json"),
    teams: Object.fromEntries(teams),
    seasons: Object.fromEntries(getSeasons().seasons.map((s) => [s.season, s])),
  };
}
