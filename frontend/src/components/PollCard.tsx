import type { Poll } from '@/types/api';
import StatusPill from './StatusPill';
import { fmtRelative, fmtCountdown } from '@/lib/format';

const colors = ['#9146ff', '#3fb950', '#e3b341', '#f85149', '#a970ff'];

export default function PollCard({ poll: p }: { poll: Poll }) {
  const total = Math.max(1, p.choices.reduce((s, c) => s + c.votes, 0));
  const maxVotes = Math.max(...p.choices.map((c) => c.votes), 1);
  const endsAt =
    p.ended_at ??
    new Date(
      new Date(p.started_at).getTime() + p.duration_seconds * 1000,
    ).toISOString();

  return (
    <article className="card p-5 space-y-4 animate-fade-up">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs text-fg-muted">
            <span className="font-mono text-fg-dim">
              tw poll · {p.twitch_poll_id.slice(-6)}
            </span>
            <span>·</span>
            <span>{fmtRelative(p.started_at)}</span>
            {p.status === 'active' && (
              <>
                <span>·</span>
                <span className="text-accent">{fmtCountdown(endsAt)} left</span>
              </>
            )}
          </div>
          <h3 className="mt-1.5 text-lg font-medium leading-snug">{p.title}</h3>
        </div>
        <StatusPill status={p.status} />
      </div>

      <div className="space-y-2">
        {p.choices.map((c, i) => {
          const pct = (c.votes / total) * 100;
          const isLeader = c.votes === maxVotes && p.status === 'active';
          return (
            <div key={c.id}>
              <div className="flex items-baseline justify-between text-sm mb-1">
                <span className={`font-medium ${isLeader ? 'text-fg' : 'text-fg-muted'}`}>
                  {c.title}
                </span>
                <span className="tabular-nums text-xs text-fg-muted">
                  {c.votes}{' '}
                  <span className="text-fg-dim">· {pct.toFixed(0)}%</span>
                </span>
              </div>
              <div className="h-2 rounded-full bg-bg-elevated overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${pct}%`,
                    background: `linear-gradient(90deg, ${colors[i % colors.length]}, ${colors[i % colors.length]}dd)`,
                    boxShadow: isLeader
                      ? `0 0 12px ${colors[i % colors.length]}66`
                      : undefined,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between text-xs text-fg-muted pt-1 border-t border-white/[0.05]">
        <span>
          {p.choices.reduce((s, c) => s + c.votes, 0)} total votes ·{' '}
          {p.twitch_status}
        </span>
        {p.suggestion_id && (
          <span className="font-mono text-fg-dim">from {p.suggestion_id}</span>
        )}
      </div>
    </article>
  );
}
