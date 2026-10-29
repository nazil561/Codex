import { useEffect, useState, useCallback } from 'react';

export type AsyncState<T> =
  | { status: 'loading' }
  | { status: 'error'; error: Error }
  | { status: 'success'; data: T };

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<AsyncState<T>>({ status: 'loading' });
  const [tick, setTick] = useState(0);
  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    // Keep showing previous data while refetching — prevents skeleton flicker
    // on live polling hooks.
    setState((prev) => (prev.status === 'success' ? prev : { status: 'loading' }));
    fn()
      .then((data) => { if (!cancelled) setState({ status: 'success', data }); })
      .catch((error: Error) => { if (!cancelled) setState({ status: 'error', error }); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { state, reload };
}
