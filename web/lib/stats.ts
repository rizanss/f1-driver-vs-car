export const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;

export function quantile(xs: number[], q: number) {
  const s = [...xs].sort((a, b) => a - b);
  const i = (s.length - 1) * q;
  const lo = Math.floor(i);
  return s[lo] + (s[Math.ceil(i)] - s[lo]) * (i - lo);
}

export const summarize = (xs: number[]) => ({ value: mean(xs), q05: quantile(xs, 0.05), q95: quantile(xs, 0.95) });

export const share = (xs: number[], test: (x: number) => boolean) => xs.filter(test).length / xs.length;

export function niceDomain(values: number[], step: number): [number, number] {
  return [Math.floor(Math.min(0, ...values) / step) * step, Math.ceil(Math.max(0, ...values) / step) * step];
}

export function ticks([lo, hi]: [number, number], step: number) {
  return Array.from({ length: Math.round((hi - lo) / step) + 1 }, (_, i) => Number((lo + i * step).toFixed(2)));
}

export function autoStep(values: number[], target = 7) {
  const width = Math.max(0, ...values) - Math.min(0, ...values);
  return [0.1, 0.2, 0.5, 1, 2].find((s) => width / s <= target) ?? 5;
}
