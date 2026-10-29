import { useState } from 'react';
import { Check, X, Sparkles, Cpu } from 'lucide-react';
import type { Suggestion } from '@/types/api';
import StatusPill from './StatusPill';
import { fmtRelative } from '@/lib/format';

type Props = {
  suggestion: Suggestion;
  busy?: boolean;
  onApprove?: (id: string) => Promise<void>;
  onReject?: (id: string) => Promise<void>;
};

function evidenceRows(e: Suggestion['evidence']) {
  return [
    { metric: `chat_messages (${e.window_minutes}m)`, value: e.chat_messages },
    { metric: `unique_chatters (${e.window_minutes}m)`, value: e.unique_chatters },
    { metric: 'latest_viewer_count', value: e.latest_viewer_count ?? '—' },
    { metric: 'chat_participation_ratio', value: e.chat_participation_ratio ?? '—' },
    { metric: 'is_live', value: String(e.is_live) },
  ];
}

export default function SuggestionCard({
  suggestion: s,
  busy,
  onApprove,
  onReject,
}: Props) {
  const [localBusy, setLocalBusy] = useState<'approve' | 'reject' | null>(null);
  const canAct = s.status === 'proposed' && !busy;
  const SourceIcon = s.source === 'openai' ? Sparkles : Cpu;

  async function handle(kind: 'approve' | 'reject') {
    setLocalBusy(kind);
    try {
      if (kind === 'approve' && onApprove) await onApprove(s.id);
      if (kind === 'reject' && onReject) await onReject(s.id);
    } finally {
      setLocalBusy(null);
    }
  }

  return (
    <article className="card p-5 space-y-4 animate-fade-up">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs text-fg-muted">
            <SourceIcon size={12} className="text-accent" />
            <span className="capitalize">{s.source === 'openai' ? 'OpenAI' : 'Rules'}</span>
            <span>·</span>
            <span>{fmtRelative(s.created_at)}</span>
          </div>
          <h3 className="mt-1.5 text-lg font-medium leading-snug">
            {s.action.title}
          </h3>
        </div>
        <StatusPill status={s.status} />
      </div>

      <div className="flex flex-wrap gap-1.5">
        {s.action.choices.map((c) => (
          <span
            key={c}
            className="text-xs rounded-full bg-bg-elevated border border-white/10 px-2.5 py-1 text-fg-muted"
          >
            {c}
          </span>
        ))}
        <span className="text-xs rounded-full bg-white/[0.03] px-2.5 py-1 text-fg-dim">
          {s.action.duration_seconds}s · real Twitch poll on approve
        </span>
      </div>

      <div className="grid md:grid-cols-2 gap-4 text-sm">
        <div>
          <div className="eyebrow">Rationale</div>
          <p className="mt-1.5 text-fg-muted leading-relaxed">{s.rationale}</p>
        </div>
        <div>
          <div className="eyebrow">Evidence</div>
          <ul className="mt-1.5 space-y-1.5">
            {evidenceRows(s.evidence).map((e, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="font-mono text-[11px] rounded bg-bg-elevated border border-white/10 px-1.5 py-0.5 text-accent shrink-0">
                  {e.metric}
                </span>
                <span className="text-fg-muted text-xs leading-relaxed">
                  <span className="text-fg font-medium">{String(e.value)}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {canAct && (
        <div className="flex gap-2 pt-1">
          <button
            onClick={() => handle('approve')}
            disabled={localBusy !== null}
            className="btn-primary text-xs"
          >
            <Check size={12} />
            {localBusy === 'approve' ? 'Creating poll…' : 'Approve & create poll'}
          </button>
          <button
            onClick={() => handle('reject')}
            disabled={localBusy !== null}
            className="btn-secondary text-xs"
          >
            <X size={12} />
            {localBusy === 'reject' ? 'Rejecting…' : 'Reject'}
          </button>
        </div>
      )}
    </article>
  );
}
