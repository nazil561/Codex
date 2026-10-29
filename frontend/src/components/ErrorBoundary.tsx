import { Component } from 'react';
import type { ReactNode, ErrorInfo } from 'react';

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Caught by ErrorBoundary:', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen grid place-items-center p-8 bg-bg text-fg">
          <div className="card p-8 max-w-lg w-full">
            <h1 className="font-display text-2xl tracking-tight text-bad">Something broke</h1>
            <p className="mt-2 text-sm text-fg-muted">{this.state.error.message}</p>
            <pre className="mt-4 text-xs text-fg-dim overflow-auto max-h-64 bg-bg-elevated p-3 rounded-lg whitespace-pre-wrap break-words">
              {this.state.error.stack}
            </pre>
            <button
              onClick={() => { this.setState({ error: null }); window.location.href = '/dashboard'; }}
              className="btn-primary mt-4"
            >
              Go to dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
