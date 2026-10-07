export const toSeconds = (pct: number, lap: number) => (pct / 100) * lap;

export function signed(x: number, digits = 2) {
  const r = Number(x.toFixed(digits));
  return `${r > 0 ? "+" : r < 0 ? "−" : ""}${Math.abs(r).toFixed(digits)}`;
}

export const sec = (x: number) => `${signed(x)} s`;
export const abs = (x: number) => `${Math.abs(x).toFixed(2)} s`;
export const faster = (x: number) => `${abs(x)} ${x >= 0 ? "faster" : "slower"}`;
export const span = (lo: number, hi: number) => `${signed(lo)} to ${signed(hi)} s`;
export const pct = (x: number) => `${Math.round(x * 100)}%`;

export function years(seasons: number[]) {
  const runs: number[][] = [];
  for (const s of seasons) {
    const run = runs.at(-1);
    if (run && s === run[run.length - 1] + 1) run.push(s);
    else runs.push([s]);
  }
  return runs.map((r) => (r.length > 1 ? `${r[0]}–${r[r.length - 1]}` : `${r[0]}`)).join(", ");
}
