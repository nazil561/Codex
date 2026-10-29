export function fmtPct(v: number | null): string {
  if (v === null || !Number.isFinite(v)) return '—';
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`;
}

export function fmtAbs(v: number | null): string {
  if (v === null || !Number.isFinite(v)) return '—';
  return Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(2);
}

export function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return iso;
  }
}

export function fmtDateRange(a: string, b: string): string {
  return `${fmtDate(a)} – ${fmtDate(b)}`;
}

export function fmtRelative(iso: string): string {
  try {
    const ms = Date.now() - new Date(iso).getTime();
    const sec = Math.floor(ms / 1000);
    if (sec < 10) return 'just now';
    if (sec < 60) return `${sec}s ago`;
    const min = Math.floor(sec / 60);
    if (min < 60) return `${min}m ago`;
    const hr = Math.floor(min / 60);
    if (hr < 24) return `${hr}h ago`;
    return `${Math.floor(hr / 24)}d ago`;
  } catch {
    return iso;
  }
}

export function fmtCountdown(iso: string): string {
  try {
    const ms = new Date(iso).getTime() - Date.now();
    if (ms <= 0) return 'ended';
    const sec = Math.floor(ms / 1000);
    const min = Math.floor(sec / 60);
    const s = sec % 60;
    if (min >= 1) return `${min}m ${s.toString().padStart(2, '0')}s`;
    return `${sec}s`;
  } catch {
    return '';
  }
}
