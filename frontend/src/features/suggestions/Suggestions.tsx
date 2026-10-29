import { useState } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import { api } from '@/api';
import { useSuggestions } from '@/hooks';
import SuggestionCard from '@/components/SuggestionCard';
import { EmptyState, ErrorState, Skeleton } from '@/components/ui';

type Filter = 'all' | 'proposed' | 'executed' | 'rejected' | 'failed';

export default function Suggestions() {
  const suggestions = useSuggestions();
  const [filter, setFilter] = useState<Filter>('all');
  const [actionErr, setActionErr] = useState<string | null>(null);
  const [suggestBusy, setSuggestBusy] = useState(false);

  async function onApprove(id: string) {
    setActionErr(null);
    try {
      await api.approveSuggestion(id);
      suggestions.reload();
    } catch (err) {
      setActionErr(err instanceof Error ? err.message : 'Approve failed');
    }
  }

  async function onReject(id: string) {
    setActionErr(null);
    try {
      await api.rejectSuggestion(id);
      suggestions.reload();
    } catch (err) {
      setActionErr(err instanceof Error ? err.message : 'Reject failed');
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

  const items = suggestions.state.status === 'success' ? suggestions.state.data : [];
  const filtered = filter === 'all' ? items : items.filter((s) => s.status === filter);

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="eyebrow">Engagement</div>
          <h1 className="mt-1.5 font-display text-4xl tracking-tight">Suggestions</h1>
          <p className="text-sm text-fg-muted mt-2 max-w-2xl">
            Poll proposals grounded in your live metrics. Approve one to launch a real Twitch poll.
          </p>
        </div>
        <button
          onClick={requestSuggestion}
          disabled={suggestBusy}
          className="btn-primary"
        >
          {suggestBusy ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
          {suggestBusy ? 'Thinking…' : 'Request suggestion'}
        </button>
      </header>

      <div className="flex flex-wrap gap-2">
        {(['all', 'proposed', 'executed', 'rejected', 'failed'] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              filter === f
                ? 'bg-accent text-white'
                : 'bg-bg-elevated text-fg-muted border border-white/10 hover:bg-white/[0.06]'
            }`}
          >
            {f[0].toUpperCase() + f.slice(1)}
            {f !== 'all' && suggestions.state.status === 'success' && (
              <span className="ml-1.5 opacity-70">
                {items.filter((s) => s.status === f).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {actionErr && (
        <div className="card p-3 text-sm text-bad border-bad/20">{actionErr}</div>
      )}

      {suggestions.state.status === 'loading' && <Skeleton className="h-40" />}
      {suggestions.state.status === 'error' && (
        <ErrorState error={suggestions.state.error} onRetry={suggestions.reload} />
      )}
      {suggestions.state.status === 'success' && filtered.length === 0 && (
        <EmptyState
          title={filter === 'all' ? 'No suggestions yet' : `No ${filter} suggestions`}
          body={
            filter === 'all'
              ? 'Press Request suggestion to ask the backend for a metrics-grounded poll proposal.'
              : 'Try a different filter to see other suggestions.'
          }
        />
      )}
      {suggestions.state.status === 'success' && filtered.length > 0 && (
        <div className="grid gap-4">
          {filtered.map((s) => (
            <SuggestionCard
              key={s.id}
              suggestion={s}
              onApprove={onApprove}
              onReject={onReject}
            />
          ))}
        </div>
      )}
    </div>
  );
}
