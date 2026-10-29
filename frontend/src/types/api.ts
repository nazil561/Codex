// Aligned to backend/PLAN.md §7 (committed contract).
// Verify against backend/contracts/examples/*.json before flipping
// VITE_USE_MOCK=false.

export type Me = {
  twitch_user_id: string;
  login: string;
  display_name: string;
  scopes: string[];
  status: 'connected' | 'disconnected' | 'expired' | 'needs_reauth';
};

export type StreamStatus = {
  is_live: boolean;
  twitch_stream_id: string | null;
  title: string | null;
  game_name: string | null;
  viewer_count: number | null;
  started_at: string | null;
  captured_at: string;
  freshness: 'live' | 'stale';
};

export type EngagementSession = {
  status: 'listening' | 'stopped';
  subscriptions: string[];
  last_gap_at: string | null;
  last_event_at?: string | null;
};

export type LiveMetrics = {
  window_minutes: number;
  window_started_at: string;
  window_ended_at: string;
  chat_messages: number;
  unique_chatters: number;
  messages_per_minute: number;
  latest_viewer_count: number | null;
  chat_participation_ratio: number | null;
  chat_participation_ratio_meaning: string;
  minutes_since_last_message: number | null;
  is_live: boolean;
  event_gap: boolean;
};

export type SuggestionStatus =
  | 'proposed' | 'approved' | 'executed' | 'rejected' | 'failed';

export type SuggestionEvidence = {
  window_minutes: number;
  chat_messages: number;
  unique_chatters: number;
  latest_viewer_count: number | null;
  chat_participation_ratio: number | null;
  is_live: boolean;
};

export type PollAction = {
  type: 'create_poll';
  title: string;
  choices: string[];
  duration_seconds: number;
};

export type Suggestion = {
  id: string;
  status: SuggestionStatus;
  source: 'openai' | 'rules';
  rationale: string;
  evidence: SuggestionEvidence;
  action: PollAction;
  created_at: string;
};

export type PollStatus =
  | 'active' | 'completed' | 'terminated' | 'archived' | 'moderated' | 'invalid';

export type PollChoice = {
  id: string;
  title: string;
  votes: number;
  channel_points_votes: number;
};

export type Poll = {
  id: string;
  suggestion_id: string | null;
  twitch_poll_id: string;
  title: string;
  status: PollStatus;
  twitch_status: string;
  duration_seconds: number;
  started_at: string;
  ended_at: string | null;
  freshness: 'live' | 'stale';
  choices: PollChoice[];
};

export type ApiErrorBody = {
  error: { code: string; message: string };
};
