import type {
  Me, StreamStatus, EngagementSession, LiveMetrics,
  Suggestion, Poll, ApiErrorBody,
} from '@/types/api';

const BASE = import.meta.env.VITE_API_BASE_URL ?? '';

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    let body: ApiErrorBody | null = null;
    try { body = (await res.json()) as ApiErrorBody; } catch { /* ignore */ }
    throw new ApiError(
      res.status,
      body?.error?.code ?? 'http_error',
      body?.error?.message ?? res.statusText,
    );
  }
  return res.json() as Promise<T>;
}

export const realApi = {
  getMe: () => request<Me>('/api/v1/me'),

  getStream: () => request<StreamStatus>('/api/v1/stream'),

  getSession: () =>
    request<EngagementSession>('/api/v1/engagement/session'),

  startSession: () =>
    request<EngagementSession>('/api/v1/engagement/session/start', {
      method: 'POST',
    }),

  stopSession: () =>
    request<EngagementSession>('/api/v1/engagement/session/stop', {
      method: 'POST',
    }),

  getMetrics: (windowMinutes = 15) =>
    request<LiveMetrics>(
      `/api/v1/metrics?window_minutes=${windowMinutes}`,
    ),

  // POST /suggestions CREATES a proposal. No Twitch side effect.
  createSuggestion: () =>
    request<Suggestion>('/api/v1/suggestions', { method: 'POST' }),

  getSuggestions: () =>
    request<Suggestion[]>('/api/v1/suggestions'),

  getSuggestion: (id: string) =>
    request<Suggestion>(`/api/v1/suggestions/${id}`),

  rejectSuggestion: (id: string) =>
    request<Suggestion>(`/api/v1/suggestions/${id}/reject`, {
      method: 'POST',
    }),

  // Approve returns THE POLL, not a suggestion wrapper.
  approveSuggestion: (id: string) =>
    request<Poll>(`/api/v1/suggestions/${id}/approve`, { method: 'POST' }),

  // GET /polls returns { "polls": [...] } — unwrap here so UI stays simple.
  getPolls: async () => {
    const body = await request<{ polls: Poll[] }>('/api/v1/polls');
    return body.polls;
  },

  getPoll: (id: string) => request<Poll>(`/api/v1/polls/${id}`),

  startOAuth: (): void => {
    // Backend returns 302 to Twitch. Must be a top-level navigation.
    window.location.href = `${BASE}/api/v1/auth/twitch/start`;
  },

  logout: () =>
    request<void>('/api/v1/auth/logout', { method: 'POST' }),
};
