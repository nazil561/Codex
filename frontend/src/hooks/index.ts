import { useEffect } from 'react';
import { api } from '@/api';
import { useAsync } from './useAsync';

export * from './useAsync';

export function useLiveAsync<T>(
  fn: () => Promise<T>,
  intervalMs = 5000,
  deps: unknown[] = [],
) {
  const result = useAsync(fn, deps);
  const { reload } = result;
  useEffect(() => {
    const id = setInterval(reload, intervalMs);
    return () => clearInterval(id);
  }, [reload, intervalMs]);
  return result;
}

export const useMe = () => useAsync(() => api.getMe(), []);
export const useStream = () => useLiveAsync(() => api.getStream(), 8000);
export const useSession = () => useAsync(() => api.getSession(), []);
export const useMetrics = (windowMinutes = 15) =>
  useLiveAsync(() => api.getMetrics(windowMinutes), 5000, [windowMinutes]);
export const useSuggestions = () => useAsync(() => api.getSuggestions(), []);
export const usePolls = () => useLiveAsync(() => api.getPolls(), 5000);
