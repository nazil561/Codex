import type { ReactNode } from 'react';

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-white/5 ${className}`} />;
}

export function EmptyState({ title, body, action }: { title: string; body?: string; action?: ReactNode }) {
  return (
    <div className="card p-10 text-center">
      <h3 className="text-lg font-medium">{title}</h3>
      {body && <p className="mt-2 text-sm text-fg-muted max-w-md mx-auto">{body}</p>}
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div className="card p-6 border-bad/20">
      <h3 className="text-sm font-semibold text-bad">Something went wrong</h3>
      <p className="mt-1 text-sm text-fg-muted">{error.message}</p>
      {onRetry && <button className="btn-secondary mt-4" onClick={onRetry}>Retry</button>}
    </div>
  );
}
