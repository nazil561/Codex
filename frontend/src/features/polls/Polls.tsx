import { usePolls } from '@/hooks';
import PollCard from '@/components/PollCard';
import { EmptyState, ErrorState, Skeleton } from '@/components/ui';
import { Link } from 'react-router-dom';

export default function Polls() {
  const polls = usePolls();

  const active = polls.state.status === 'success' ? polls.state.data.filter((p) => p.status === 'active') : [];
  const completed = polls.state.status === 'success' ? polls.state.data.filter((p) => p.status !== 'active') : [];

  return (
    <div className="space-y-6">
      <header>
        <div className="eyebrow">Live engagement</div>
        <h1 className="mt-1.5 font-display text-4xl tracking-tight">Polls</h1>
        <p className="text-sm text-fg-muted mt-2 max-w-2xl">
          Polls created from approved suggestions. Vote totals update in real time from Twitch EventSub.
        </p>
      </header>

      {polls.state.status === 'loading' && <Skeleton className="h-40" />}
      {polls.state.status === 'error' && <ErrorState error={polls.state.error} onRetry={polls.reload} />}
      {polls.state.status === 'success' && polls.state.data.length === 0 && (
        <EmptyState
          title="No polls yet"
          body="Approve a suggestion to create a real Twitch poll. Votes will appear here in real time."
          action={<Link to="/suggestions" className="btn-primary">View suggestions</Link>}
        />
      )}

      {active.length > 0 && (
        <section>
          <h2 className="eyebrow mb-3">Active</h2>
          <div className="grid gap-4">
            {active.map((p) => <PollCard key={p.id} poll={p} />)}
          </div>
        </section>
      )}

      {completed.length > 0 && (
        <section>
          <h2 className="eyebrow mb-3">Past polls</h2>
          <div className="grid gap-4">
            {completed.map((p) => <PollCard key={p.id} poll={p} />)}
          </div>
        </section>
      )}
    </div>
  );
}
