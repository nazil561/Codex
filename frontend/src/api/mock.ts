import type {
  Me, StreamStatus, EngagementSession, LiveMetrics,
  Suggestion, Poll,
} from '@/types/api';

const now = Date.now();
const min = 60_000;

export const demoMe: Me = {
  twitch_user_id: '99999999',
  login: 'demo_streamer',
  display_name: 'DemoStreamer',
  scopes: [
    'user:read:chat',
    'channel:manage:polls',
    'channel:read:polls',
  ],
  status: 'connected',
};

export const demoStream = (live: boolean): StreamStatus =>
  live
    ? {
        is_live: true,
        twitch_stream_id: 'stream-demo-001',
        title: 'Late night ranked grind',
        game_name: "Baldur's Gate 3",
        viewer_count: 245,
        started_at: new Date(now - 47 * min).toISOString(),
        captured_at: new Date().toISOString(),
        freshness: 'live',
      }
    : {
        is_live: false,
        twitch_stream_id: null,
        title: null,
        game_name: null,
        viewer_count: null,
        started_at: null,
        captured_at: new Date().toISOString(),
        freshness: 'live',
      };

export const demoSession = (active: boolean): EngagementSession =>
  active
    ? {
        status: 'listening',
        subscriptions: [
          'channel.chat.message',
          'channel.poll.begin',
          'channel.poll.progress',
          'channel.poll.end',
        ],
        last_gap_at: null,
        last_event_at: new Date(now - 8_000).toISOString(),
      }
    : {
        status: 'stopped',
        subscriptions: [],
        last_gap_at: null,
        last_event_at: null,
      };

let metricTick = 0;
export function demoMetrics(windowMinutes = 15): LiveMetrics {
  metricTick++;
  const t = metricTick / 3;
  const jitter = Math.sin(t) * 5 + Math.sin(t * 2.3) * 2;
  const chat = Math.max(20, Math.round(87 + jitter * 2));
  const viewers = Math.max(50, Math.round(245 + jitter * 3));
  return {
    window_minutes: windowMinutes,
    window_started_at: new Date(now - windowMinutes * min).toISOString(),
    window_ended_at: new Date().toISOString(),
    chat_messages: chat,
    unique_chatters: Math.max(5, Math.round(34 + jitter / 2)),
    messages_per_minute: Math.round((chat / windowMinutes) * 100) / 100,
    latest_viewer_count: viewers,
    chat_participation_ratio:
      Math.round((34 / Math.max(1, viewers)) * 100) / 100,
    chat_participation_ratio_meaning:
      'unique chatters divided by the latest sampled viewer count; not retention or churn',
    minutes_since_last_message: 0,
    is_live: true,
    event_gap: false,
  };
}

const mkSug = (
  o: Partial<Suggestion> & {
    id: string;
    status: Suggestion['status'];
    title: string;
    choices: string[];
    duration_seconds: number;
  },
): Suggestion => ({
  source: 'openai',
  rationale:
    'Chat activity dipped while a longer in-game segment ran. A short, chat-driven poll usually converts silent viewers into participants within 30 seconds.',
  evidence: {
    window_minutes: 15,
    chat_messages: 72,
    unique_chatters: 31,
    latest_viewer_count: 245,
    chat_participation_ratio: 0.13,
    is_live: true,
  },
  created_at: new Date(now - 10 * min).toISOString(),
  ...o,
  action: {
    type: 'create_poll',
    title: o.title,
    choices: o.choices,
    duration_seconds: o.duration_seconds,
  },
});

export const demoSuggestions: Suggestion[] = [
  mkSug({
    id: 'sug-001',
    status: 'proposed',
    title: 'Which segment should we run next?',
    choices: ['Boss attempts', 'Chat challenges', 'Q&A'],
    duration_seconds: 120,
    created_at: new Date(now - 8 * min).toISOString(),
  }),
  mkSug({
    id: 'sug-002',
    status: 'proposed',
    source: 'rules',
    title: 'Difficulty next run?',
    choices: ['Tactician', 'Balanced', 'Story mode'],
    duration_seconds: 90,
    created_at: new Date(now - 22 * min).toISOString(),
    rationale:
      'The last three encounters took over six minutes each and generated a spike in frustration emotes. Giving chat the difficulty dial often re-engages lurkers.',
    evidence: {
      window_minutes: 15,
      chat_messages: 64,
      unique_chatters: 29,
      latest_viewer_count: 238,
      chat_participation_ratio: 0.12,
      is_live: true,
    },
  }),
  mkSug({
    id: 'sug-003',
    status: 'executed',
    title: 'Warmup game?',
    choices: ['LoL', 'Valorant', 'TFT'],
    duration_seconds: 60,
    created_at: new Date(now - 45 * min).toISOString(),
  }),
  mkSug({
    id: 'sug-004',
    status: 'rejected',
    source: 'rules',
    title: 'Add a facecam?',
    choices: ['Yes', 'No'],
    duration_seconds: 60,
    created_at: new Date(now - 90 * min).toISOString(),
    rationale:
      'Facecam polls help when viewer count is growing — not the case right now.',
    evidence: {
      window_minutes: 15,
      chat_messages: 41,
      unique_chatters: 18,
      latest_viewer_count: 245,
      chat_participation_ratio: 0.07,
      is_live: true,
    },
  }),
];

const mkPoll = (
  o: Omit<Partial<Poll>, 'choices'> & {
    id: string;
    title: string;
    status: Poll['status'];
    started_at: string;
    duration_seconds: number;
    choices: { id: string; title: string; votes: number }[];
  },
): Poll => ({
  suggestion_id: null,
  twitch_poll_id: `tw-poll-${o.id}`,
  twitch_status: o.status === 'active' ? 'ACTIVE' : 'COMPLETED',
  ended_at: null,
  freshness: 'live',
  ...o,
  choices: o.choices.map((c) => ({ ...c, channel_points_votes: 0 })),
});

let pollTick = 0;
export const demoPolls = (): Poll[] => {
  pollTick++;
  const bump = Math.floor(pollTick / 2);
  return [
    mkPoll({
      id: 'poll-001',
      suggestion_id: 'sug-003',
      title: 'Warmup game?',
      status: 'active',
      started_at: new Date(now - 3 * min).toISOString(),
      duration_seconds: 120,
      choices: [
        { id: 'c1', title: 'LoL', votes: 18 + bump },
        { id: 'c2', title: 'Valorant', votes: 42 + bump * 2 },
        { id: 'c3', title: 'TFT', votes: 11 + bump },
      ],
    }),
    mkPoll({
      id: 'poll-000',
      title: 'Break length?',
      status: 'completed',
      started_at: new Date(now - 40 * min).toISOString(),
      duration_seconds: 120,
      ended_at: new Date(now - 38 * min).toISOString(),
      choices: [
        { id: 'c1', title: '5 min', votes: 24 },
        { id: 'c2', title: '10 min', votes: 61 },
        { id: 'c3', title: '15 min', votes: 8 },
      ],
    }),
  ];
};
