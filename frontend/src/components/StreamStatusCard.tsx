import { Radio, Users, Gamepad2, Clock } from 'lucide-react';
import type { StreamStatus } from '@/types/api';
import StatusPill from './StatusPill';
import { fmtRelative } from '@/lib/format';

export default function StreamStatusCard({ stream }: { stream: StreamStatus }) {
  return (
    <div className="card p-5 flex items-center gap-4">
      <div
        className={`h-12 w-12 rounded-xl grid place-items-center shrink-0 ${
          stream.is_live
            ? 'bg-bad/10 ring-1 ring-inset ring-bad/30'
            : 'bg-bg-elevated ring-1 ring-inset ring-white/10'
        }`}
      >
        <Radio
          size={20}
          className={stream.is_live ? 'text-bad' : 'text-fg-dim'}
        />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <StatusPill status={stream.is_live ? 'live' : 'offline'} />
          {stream.is_live && stream.started_at && (
            <span className="text-xs text-fg-muted flex items-center gap-1">
              <Clock size={10} /> {fmtRelative(stream.started_at)}
            </span>
          )}
        </div>
        <div className="mt-1 font-medium truncate">
          {stream.is_live ? (stream.title ?? 'Untitled stream') : 'Not streaming'}
        </div>
        {stream.is_live && (
          <div className="mt-1 flex items-center gap-4 text-xs text-fg-muted">
            {stream.game_name && (
              <span className="flex items-center gap-1">
                <Gamepad2 size={11} /> {stream.game_name}
              </span>
            )}
            {typeof stream.viewer_count === 'number' && (
              <span className="flex items-center gap-1">
                <Users size={11} /> {stream.viewer_count}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
