import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/api';
import { useMe } from '@/hooks';
import { ErrorState, Skeleton } from '@/components/ui';
import { fmtRelative } from '@/lib/format';

export default function Settings() {
  const me = useMe();
  const lastChecked = useMemo(() => new Date().toISOString(), []);
  const nav = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function logout() {
    if (!confirm('Disconnect Twitch? You can reconnect at any time.')) return;
    setBusy(true);
    setError(null);
    try {
      await api.logout();
      me.reload();
      nav('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Logout failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <header>
        <div className="eyebrow">Account</div>
        <h1 className="mt-1.5 font-display text-4xl tracking-tight">Settings</h1>
        <p className="text-sm text-fg-muted mt-2">Connection, permissions, and data handling.</p>
      </header>

      {me.state.status === 'loading' && <Skeleton className="h-40" />}
      {me.state.status === 'error' && <ErrorState error={me.state.error} onRetry={me.reload} />}
      {me.state.status === 'success' && (
        <>
          <section className="card p-5">
            <h2 className="font-medium">Twitch connection</h2>
            <div className="mt-3 text-sm space-y-1.5">
              <div>
                <span className="text-fg-muted">Status: </span>
                {me.state.data.status === 'connected'
                  ? <span className="text-ok">Connected</span>
                  : <span className="text-bad">Disconnected</span>}
              </div>
              {me.state.data.login && (
                <div><span className="text-fg-muted">Login: </span><span className="font-mono text-xs">{me.state.data.login}</span></div>
              )}
              {me.state.data.display_name && (
                <div><span className="text-fg-muted">Channel: </span>{me.state.data.display_name}</div>
              )}
              {me.state.data.twitch_user_id && (
                <div><span className="text-fg-muted">Twitch user ID: </span><span className="font-mono text-xs">{me.state.data.twitch_user_id}</span></div>
              )}
            </div>
            {error && <p className="text-sm text-bad mt-3">{error}</p>}
            <div className="mt-4">
              {me.state.data.status === 'connected' ? (
                <button onClick={logout} disabled={busy} className="btn-secondary">
                  {busy ? 'Disconnecting…' : 'Disconnect Twitch'}
                </button>
              ) : (
                <button onClick={() => api.startOAuth()} className="btn-primary">
                  Connect Twitch
                </button>
              )}
            </div>
          </section>

          <section className="card p-5">
            <h2 className="font-medium">Granted scopes</h2>
            <ul className="mt-3 flex flex-wrap gap-1.5">
              {me.state.data.scopes.length === 0 && <li className="text-sm text-fg-muted">No scopes granted.</li>}
              {me.state.data.scopes.map((s) => (
                <li key={s} className="font-mono text-[11px] bg-bg-elevated border border-white/10 px-2 py-1 rounded text-fg-muted">{s}</li>
              ))}
            </ul>
          </section>

          <section className="card p-5">
            <h2 className="font-medium">Privacy & data handling</h2>
            <ul className="mt-3 text-sm text-fg-muted list-disc pl-5 space-y-1 leading-relaxed">
              <li>We read chat and poll events through Twitch EventSub during active listening sessions.</li>
              <li>We never identify individual returning viewers. Twitch does not provide that data to third-party apps.</li>
              <li>Session cookies are HttpOnly and SameSite=Lax. Twitch access tokens never reach the browser.</li>
              <li>Disconnecting removes the session cookie. You can revoke scopes on Twitch at any time.</li>
            </ul>
          </section>

          {me.state.data.login && (
            <div className="text-xs text-fg-dim">
              Demo mode notice: sample data only. Status refreshes every page load.
              {me.state.data.status === 'connected' && ` · last checked ${fmtRelative(lastChecked)}`}
            </div>
          )}
        </>
      )}
    </div>
  );
}
