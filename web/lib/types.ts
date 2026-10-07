export type DriverRating = { driver: string; season: number; teams: string[]; rating: number; q05: number; q95: number };
export type CarRating = { team: string; season: number; rating: number; q05: number; q95: number };
export type SeasonInfo = { season: number; car_share: number; q05: number; q95: number; pole_lap: number; rounds: number };
export type EraInfo = { era: string; car_share: number; q05: number; q95: number };
export type Person = { name: string; headshot: string | null };
export type DriverDraws = { driver: string; season: number; draws: number[] };
export type CarDraws = { team: string; season: number; draws: number[] };
export type Team = { lineage: string; color: string };

export type Network = {
  teams: { id: string; color: string; names: string[] }[];
  drivers: { id: string }[];
  links: { source: string; target: string; seasons: number[] }[];
};

export type Shared = {
  people: Record<string, Person>;
  teams: Record<string, Team>;
  seasons: Record<number, SeasonInfo>;
};
