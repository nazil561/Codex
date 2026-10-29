export function pctChange(baseline: number, followUp: number): number | null {
  if (!Number.isFinite(baseline) || baseline === 0) return null;
  return ((followUp - baseline) / Math.abs(baseline)) * 100;
}

export function absChange(baseline: number, followUp: number): number {
  return followUp - baseline;
}
