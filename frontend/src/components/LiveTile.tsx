import { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { isDemoMode } from '@/api';
import Sparkline from './Sparkline';

type Props = {
  label: string;
  value: number;
  unit?: string;
  higherIsBetter?: boolean;
  seed?: number;
};

export default function LiveTile({ label, value, unit, higherIsBetter = true, seed }: Props) {
  const [history, setHistory] = useState<number[]>(() => {
    if (isDemoMode) {
      return Array.from({ length: 20 }, (_, i) =>
        value + Math.sin(i / 3 + (seed ?? 0)) * Math.max(1, value * 0.05),
      );
    }
    return [value];
  });

  useEffect(() => {
    setHistory((prev) => {
      const next = [...prev, value];
      return next.length > 40 ? next.slice(-40) : next;
    });
  }, [value]);

  const oldest = history[0] ?? value;
  const delta = oldest !== 0 ? ((value - oldest) / Math.abs(oldest)) * 100 : null;
  const positive = delta !== null ? (higherIsBetter ? delta >= 0 : delta <= 0) : null;

  return (
    <div className="card card-hover p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs text-fg-muted truncate">{label}</div>
          {unit && (
            <div className="text-[10px] text-fg-dim uppercase tracking-wider mt-0.5">
              {unit}
            </div>
          )}
        </div>
        {delta !== null && (
          <span
            className={`inline-flex items-center gap-0.5 text-[11px] font-medium shrink-0 ${
              positive ? 'text-ok' : 'text-bad'
            }`}
          >
            {positive ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
            {Math.abs(delta).toFixed(1)}%
          </span>
        )}
      </div>
      <div className="mt-2 font-display text-3xl tabular-nums leading-none">{value}</div>
      <div className="mt-2 -mx-1">
        <Sparkline data={history} height={32} />
      </div>
    </div>
  );
}
