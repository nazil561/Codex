import type {
  Me, StreamStatus, EngagementSession, LiveMetrics,
  Suggestion, Poll,
} from '@/types/api';
import {
  demoMe, demoStream, demoSession, demoMetrics,
  demoSuggestions, demoPolls,
} from './mock';

const delay = (ms = 200) => new Promise<void>((r) => setTimeout(r, ms));

let connected = true;
let sessionActive = true;
let streamLive = true;
let suggestions: Suggestion[] = demoSuggestions.map((s) => ({
  ...s,
  action: { ...s.action, choices: [...s.action.choices] },
  evidence: { ...s.evidence },
}));
let polls: Poll[] = demoPolls().map((p) => ({
  ...p,
  choices: p.choices.map((c) => ({ ...c })),
}));

export const mockApi = {
  getMe: async (): Promise<Me> => {
    await delay();
    return {
      ...demoMe,
      status: connected ? 'connected' : 'disconnected',
    };
  },

  getStream: async (): Promise<StreamStatus> => {
    await delay();
    return demoStream(streamLive);
  },

  getSession: async (): Promise<EngagementSession> => {
    await delay();
    return demoSession(sessionActive);
  },

  startSession: async (): Promise<EngagementSession> => {
    await delay();
    sessionActive = true;
    return demoSession(true);
  },

  stopSession: async (): Promise<EngagementSession> => {
    await delay();
    sessionActive = false;
    return demoSession(false);
  },

  getMetrics: async (windowMinutes = 15): Promise<LiveMetrics> => {
    await delay(150);
    return demoMetrics(windowMinutes);
  },

  // POST /suggestions — create a proposal.
  createSuggestion: async (): Promise<Suggestion> => {
    await delay();
    const title =
      ['What should we do next?', 'Next challenge?', 'Chat decides?'][
        Math.floor(Math.random() * 3)
      ];
    const choices = [
      ['Boss fight', 'Viewer challenge'],
      ['Ranked', 'Casual', 'Co-op'],
      ['Speedrun', 'Lore run'],
    ][Math.floor(Math.random() * 3)];
    const sug: Suggestion = {
      id: `sug-${Math.random().toString(36).slice(2, 7)}`,
      status: 'proposed',
      source: Math.random() > 0.4 ? 'openai' : 'rules',
      rationale:
        'Chat volume dropped while a long segment ran. A short poll gives lurkers a low-effort way to participate.',
      evidence: {
        window_minutes: 15,
        chat_messages: 68,
        unique_chatters: 27,
        latest_viewer_count: 243,
        chat_participation_ratio: 0.11,
        is_live: true,
      },
      action: {
        type: 'create_poll',
        title,
        choices,
        duration_seconds: 60,
      },
      created_at: new Date().toISOString(),
    };
    suggestions = [sug, ...suggestions];
    return sug;
  },

  getSuggestions: async (): Promise<Suggestion[]> => {
    await delay();
    return suggestions.map((s) => ({
      ...s,
      action: { ...s.action, choices: [...s.action.choices] },
      evidence: { ...s.evidence },
    }));
  },

  getSuggestion: async (id: string): Promise<Suggestion> => {
    await delay();
    const s = suggestions.find((x) => x.id === id);
    if (!s) throw new Error('Suggestion not found');
    return s;
  },

  rejectSuggestion: async (id: string): Promise<Suggestion> => {
    await delay();
    const i = suggestions.findIndex((s) => s.id === id);
    if (i < 0) throw new Error('Suggestion not found');
    if (suggestions[i].status !== 'proposed')
      throw new Error('suggestion_not_pending');
    suggestions[i] = { ...suggestions[i], status: 'rejected' };
    return suggestions[i];
  },

  // Approve returns the poll.
  approveSuggestion: async (id: string): Promise<Poll> => {
    await delay();
    const i = suggestions.findIndex((s) => s.id === id);
    if (i < 0) throw new Error('Suggestion not found');
    if (suggestions[i].status !== 'proposed')
      throw new Error('suggestion_not_pending');
    const sug = suggestions[i];
    suggestions[i] = { ...sug, status: 'executed' };
    const poll: Poll = {
      id: `poll-${Math.random().toString(36).slice(2, 7)}`,
      suggestion_id: sug.id,
      twitch_poll_id: `tw-poll-${Math.random().toString(36).slice(2, 8)}`,
      title: sug.action.title,
      status: 'active',
      twitch_status: 'ACTIVE',
      duration_seconds: sug.action.duration_seconds,
      started_at: new Date().toISOString(),
      ended_at: null,
      freshness: 'live',
      choices: sug.action.choices.map((title, idx) => ({
        id: `c${idx}`,
        title,
        votes: 0,
        channel_points_votes: 0,
      })),
    };
    polls = [poll, ...polls];
    return poll;
  },

  getPolls: async (): Promise<Poll[]> => {
    await delay();
    const fresh = demoPolls();
    polls = polls.map((p) => {
      const f = fresh.find((x) => x.id === p.id);
      return f ? f : p;
    });
    return polls.map((p) => ({
      ...p,
      choices: p.choices.map((c) => ({ ...c })),
    }));
  },

  getPoll: async (id: string): Promise<Poll> => {
    await delay();
    const p = polls.find((x) => x.id === id);
    if (!p) throw new Error('Poll not found');
    return p;
  },

  startOAuth: (): void => {
    connected = true;
    window.location.href = '/dashboard';
  },

  logout: async (): Promise<void> => {
    await delay();
    connected = false;
    sessionActive = false;
    streamLive = false;
  },
};
