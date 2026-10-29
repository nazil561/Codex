import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, Square, ArrowRight, Sparkles, Radio, Loader2 } from 'lucide-react';
import { api } from '@/api';
import {
  useMe, useStream, useSession, useMetrics, useSuggestions, usePolls,
} from '@/hooks';
import StreamStatusCard from '@/components/StreamStatusCard';
import LiveTile from '@/components/LiveTile';
import { EmptyState, ErrorState, Skeleton } from '@/components/ui';

export default function Dashboard() {
  const me = useMe();
  const stream = useStream();
  const session = useSession();
  const metrics = useMetrics(15);
  const suggestions = useSuggestions();
  const polls = usePolls();

  const [busy, setBusy] = useState(false);
  const [suggestBusy, setSuggestBusy] = useState(false);
  const [actionErr, setActionErr] = useState<string | null>(null);

  async function toggleSession() {
    if (session.state.status !== 'success') return;
    setBusy(true);
    setActionErr(null);
    try {
      if (session.state.data.status === 'listening') await api.stopSession();
      else await api.startSession();
      session.reload();
      stream.reload();
    } catch (err) {
      setActionErr(err instanceof Error ? err.message : 'Session toggle failed');
    } finally {
      setBusy(false);
    }
  }

  async function requestSuggestion() {
    setSuggestBusy(true);
    setActionErr(null);
    try {
      await api.createSuggestion();
      suggestions.reload();
    } catch (err) {
      setActionErr(err instanceof Error ? err.message : 'Suggestion failed');
    } finally {
      setSuggestBusy(false);
    }
  }

  const pendingCount =
    suggestions.state.status === 'success'
      ? suggestions.state.data.filter((s) => s.status === 'proposed').length
      : 0;
  const activePolls =
    polls.state.status === 'success'
      ? polls.state.data.filter((p) => p.status === 'active').length
      : 0;
  const sessionActive =
    session.state.status === 'success' && session.state.data.status === 'listening';

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="eyebrow">Overview</div>
          <h1 className="mt-1.5 font-display text-4xl tracking-tight">Dashboard</h1>
          <p className="text-sm text-fg-muted mt-1">
            {me.state.status === 'success' && me.state.data.status === 'connected'
              ? `Connected as ${me.state.data.display_name ?? me.state.data.login}.`
              : 'Connect Twitch to get started.'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={requestSuggestion}
            disabled={suggestBusy || !sessionActive}
            className="btn-secondary"
            title={!sessionActive ? 'Start listening first' : 'Ask the backend for a proposal'}
          >
            {suggestBusy ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {suggestBusy ? 'Thinking…' : 'Suggest now'}
          </button>
          {sessionActive ? (
            <button onClick={toggleSession} disabled={busy} className="btn-secondary">
              <Square size={14} /> {busy ? 'Stopping…' : 'Stop listening'}
            </button>
          ) : (
            <button onClick={toggleSession} disabled={busy} className="btn-primary">
              <Play size={14} /> {busy ? 'Starting…' : 'Start listening'}
            </button>
          )}
        </div>
      </header>

      {actionErr && (
        <div className="card p-3 text-sm text-bad border-bad/20">{actionErr}</div>
      )}

      {stream.state.status === 'loading' && <Skeleton className="h-24" />}
      {stream.state.status === 'error' && (
        <ErrorState error={stream.state.error} onRetry={stream.reload} />
      )}
      {stream.state.status === 'success' && <StreamStatusCard stream={stream.state.data} />}

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="eyebrow">Live metrics · last 15 min</h2>
          {sessionActive && (
            <span className="inline-flex items-center gap-1.5 text-xs text-accent">
              <Radio size={11} className="animate-pulse-soft" /> listening
            </span>
          )}
        </div>
        {!sessionActive && session.state.status === 'success' && (
          <div className="card p-6 text-center text-sm text-fg-muted">
            Start listening to see live metrics from Twitch EventSub.
          </div>
        )}
        {sessionActive && metrics.state.status === 'loading' && (
          <div className="grid md:grid-cols-3 gap-3">
            <Skeleton className="h-32" /><Skeleton className="h-32" /><Skeleton className="h-32" />
          </div>
        )}
        {sessionActive && metrics.state.status === 'error' && (
          <ErrorState error={metrics.state.error} onRetry={metrics.reload} />
        )}
        {sessionActive && metrics.state.status === 'success' && (
          <div className="grid md:grid-cols-3 gap-3">
            <LiveTile
              label="Chat messages"
              value={metrics.state.data.chat_messages}
              unit="15 min"
              seed={0}
            />
            <LiveTile
              label="Unique chatters"
              value={metrics.state.data.unique_chatters}
              unit="15 min"
              seed={1.4}
            />
            <LiveTile
              label="Viewer count"
              value={metrics.state.data.latest_viewer_count ?? 0}
              unit="live"
              seed={2.1}
            />
          </div>
        )}
      </section>

      <section className="grid md:grid-cols-2 gap-3">
        <Link to="/suggestions" className="card card-hover p-5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="h-10 w-10 rounded-lg bg-accent-soft grid place-items-center shrink-0">
              <Sparkles size={18} className="text-accent" />
            </div>
            <div className="min-w-0">
              <div className="font-medium">Suggestions</div>
              <div className="text-xs text-fg-muted">
                {pendingCount > 0 ? `${pendingCount} pending` : 'No pending suggestions'}
              </div>
            </div>
          </div>
          <ArrowRight size={16} className="text-fg-dim shrink-0" />
        </Link>
        <Link to="/polls" className="card card-hover p-5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="h-10 w-10 rounded-lg bg-bg-elevated grid place-items-center shrink-0">
              <Radio size={18} className={activePolls > 0 ? 'text-accent' : 'text-fg-muted'} />
            </div>
            <div className="min-w-0">
              <div className="font-medium">Polls</div>
              <div className="text-xs text-fg-muted">
                {activePolls > 0 ? `${activePolls} active` : 'No active polls'}
              </div>
            </div>
          </div>
          <ArrowRight size={16} className="text-fg-dim shrink-0" />
        </Link>
      </section>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="eyebrow">Pending suggestions</h2>
          <Link to="/suggestions" className="text-xs text-accent hover:underline">View all</Link>
        </div>
        {suggestions.state.status === 'success' && pendingCount === 0 && (
          <EmptyState
            title="No pending suggestions"
            body="Start listening, then press Suggest now to ask for a metrics-grounded poll proposal."
            action={<Link to="/suggestions" className="btn-secondary">See all suggestions</Link>}
          />
        )}
        {suggestions.state.status === 'success' && pendingCount > 0 && (
          <ul className="card divide-y divide-white/[0.05] overflow-hidden">
            {suggestions.state.data
              .filter((s) => s.status === 'proposed')
              .map((s) => (
                <li key={s.id}>
                  <Link
                    to="/suggestions"
                    className="flex items-center gap-4 px-5 py-4 hover:bg-white/[0.02] transition-colors group"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate group-hover:text-accent transition-colors">
                        {s.action.title}
                      </div>
                      <div className="text-xs text-fg-muted truncate mt-0.5">
                        {s.action.choices.join(' · ')}
                      </div>
                    </div>
                    <ArrowRight size={14} className="text-fg-dim shrink-0" />
                  </Link>
                </li>
              ))}
          </ul>
        )}
      </section>
    </div>
  );
}
