---
name: Engagement Coach Backend
overview: "Build a single-process FastAPI backend for Live Engagement Coach: Twitch OAuth, EventSub over WebSocket, minute-level engagement aggregates, an approved-only poll action, and an OpenAPI contract the frontend can mock. No application code exists yet, and nothing will be implemented until this plan is approved."
todos:
  - id: phase-0-prereqs
    content: "Human prerequisites: Docker or Python 3.12 plus Postgres, Twitch confidential app, OpenAI key or rules-only decision"
    status: pending
  - id: phase-1-skeleton
    content: FastAPI skeleton, Compose, health route, OpenAPI export, and committed JSON examples
    status: pending
  - id: phase-2-schema
    content: SQLAlchemy models and Alembic initial migration for accounts, events, metrics, suggestions, and polls
    status: pending
  - id: phase-3-oauth
    content: Authorization-code OAuth, state checks, encrypted tokens, and session cookie
    status: pending
  - id: phase-4-helix
    content: Helix client for users, streams, refresh, validate, and rate-limit errors
    status: pending
  - id: phase-5-eventsub
    content: WebSocket EventSub listener, dedup, and minute engagement aggregates
    status: pending
  - id: phase-6-suggestions
    content: Metrics-grounded suggestions with OpenAI and rules fallback, no Twitch side effects
    status: pending
  - id: phase-7-polls
    content: Explicit approve path that creates a Twitch poll and exposes results
    status: pending
  - id: phase-8-docs-demo
    content: README runbook and demo script that satisfy hackathon submission requirements
    status: pending
isProject: false
---

# Live Engagement Coach Backend Plan

Planning only. No source files, dependencies, or migrations will be created until this plan is approved.

Submission window is 23 Oct 2026 10:00 Pacific through 2 Nov 2026 14:00 Pacific ([official rules](https://twitchcon-codex.devpost.com/rules)). Today is 28 Oct 2026, so about five days remain. This Cursor planning session is not a Codex session and cannot be submitted as the required Codex session ID.

## 1. Repository and environment assessment

- Workspace `D:\devpost\Codex` is a git repo on `main`, clean, tracking `origin` at `https://github.com/nazil561/Codex.git`.
- The only commit is `bb693a8` (`Initial commit`, author `nazil561`, 27 Oct 2026 10:38 +0530). That timestamp is inside the submission window. The commit adds one file: [README.md](README.md), whose entire content is `# Codex`.
- There is no application code, dependency file, schema, secret, Twitch app config, or frontend. Nothing in this repo is reusable product work. Do not import code from any other project.
- You will create a `backend/` directory for this service. All Python code, Compose, Alembic, tests, the OpenAPI contract, and the backend runbook go there. The repo root stays a short project index so a frontend can be added beside it later. Implementation will not scaffold a frontend and will not put the service at the repo root.
- Host Python is `3.11.0` (`python` and `py -3`). The `docker` command is not installed. PostgreSQL was not detected as a running local service during this inspection.
- Target runtime remains Python 3.12 in the Docker image, even though the host interpreter is 3.11. Local execution depends on installing Docker Desktop, or installing Python 3.12 plus PostgreSQL outside Docker. That install is a prerequisite, not part of this planning step.
- No credentials, Twitch application, OpenAI key, database, or public deployment URL exist in the repo. Do not assume they exist on the machine.
- Likely delivery shape: one local Docker Compose stack for development and judging, plus one public HTTPS deployment only if the demo needs a stable URL. Judges may score from the YouTube video and are not required to run the project. The repo must still contain source and run instructions.

## 2. Recommended MVP and user workflow

One vertical slice, one Twitch account, one process.

Minimum successful demonstration:

1. Streamer opens the frontend and chooses Connect Twitch.
2. Backend completes the authorization-code flow and stores encrypted tokens.
3. Backend reads the authenticated user and whether that channel is live.
4. Streamer starts listening. Backend opens one EventSub WebSocket and subscribes to that channel’s chat and poll events.
5. Chat events increment minute buckets. Message text is discarded.
6. Streamer asks for a suggestion. The suggestion cites the stored aggregates and proposes one poll.
7. Nothing is sent to Twitch until the streamer approves that exact suggestion.
8. Approval calls Create Poll. The native Twitch poll appears on the live channel.
9. Poll progress and end events, plus Get Polls, update stored results.
10. Frontend reads the poll and vote totals from our API.

Mandatory:

- OAuth authorization-code flow, session cookie, encrypted token storage, reactive refresh, hourly token validation.
- Current stream lookup via Get Streams, with an explicit offline state.
- EventSub WebSocket for `channel.chat.message` v1 and `channel.poll.begin`, `channel.poll.progress`, `channel.poll.end` v1.
- Minute aggregates and a metrics read API.
- One suggestion at a time, either from OpenAI or from a rules fallback, never auto-executed.
- Approve creates one real poll. Reject does not. Results are readable after votes arrive.
- OpenAPI schema and committed JSON examples so the frontend can mock immediately.
- Automated tests that never call live Twitch.

Explicit non-goals for the MVP:

- Webhook transport, Conduits, a second unscoped token, IRC chat, Send Chat Message, predictions, Channel Points voting, follows, subscriptions, cheers, raids, and overlays.
- Multiple concurrent streamers beyond a schema that can store more than one account. The demo runs one listener.
- Redis, Celery, Kafka, or more than one API replica. WebSocket state lives in the API process.
- Storing chat text, emails, or a claim that chat volume measures retention or individual churn.

Graceful fallbacks:

- Missing `OPENAI_API_KEY`, timeout, or invalid model output: store a rules-based poll suggestion and set `source` to `rules`.
- Channel offline: metrics and suggestions still load; approve returns `409` with `stream_offline` and does not call Create Poll. Whether Twitch accepts polls while offline was not verified, so the MVP refuses that case.
- EventSub subscribe fails or a required scope is missing: listening status becomes `degraded` with a safe `missing_scope` or `eventsub_unavailable` code. Stream snapshots can still refresh.
- Twitch `401`: refresh once under a per-account lock, retry the call once, then mark the account `needs_reauth` and stop the listener.
- Twitch `429`: surface `twitch_rate_limited` and do not tight-loop.
- Create Poll says a poll is already running: return `409 poll_already_active` and do not create a second suggestion execution.

User workflow:

```mermaid
sequenceDiagram
  participant Streamer
  participant Frontend
  participant Api as FastAPI
  participant Twitch
  participant Model as OpenAI_or_rules
  Streamer->>Frontend: Connect Twitch
  Frontend->>Api: GET /api/v1/auth/twitch/start
  Api->>Twitch: Authorize redirect
  Twitch->>Api: Callback with code and state
  Api->>Twitch: Exchange code
  Api->>Frontend: Session cookie and redirect
  Streamer->>Frontend: Start listening
  Frontend->>Api: POST /api/v1/engagement/session/start
  Api->>Twitch: EventSub WebSocket subscribe
  Twitch-->>Api: Chat and poll events
  Api->>Api: Aggregate counts only
  Streamer->>Frontend: Suggest
  Frontend->>Api: POST /api/v1/suggestions
  Api->>Model: Aggregates only
  Model-->>Api: Poll proposal
  Streamer->>Frontend: Approve
  Frontend->>Api: POST /api/v1/suggestions/{id}/approve
  Api->>Twitch: Create Poll
  Twitch-->>Api: Poll progress and end
  Frontend->>Api: GET /api/v1/polls/{id}
```

## 3. Verified Twitch API requirements

Primary sources checked on 28 Oct 2026: [Authentication](https://dev.twitch.tv/docs/authentication/), [Getting tokens](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/), [Refresh](https://dev.twitch.tv/docs/authentication/refresh-tokens/), [Validate](https://dev.twitch.tv/docs/authentication/validate-tokens/), [API reference](https://dev.twitch.tv/docs/api/reference), [API guide rate limits](https://dev.twitch.tv/docs/api/guide), [EventSub](https://dev.twitch.tv/docs/eventsub/), [WebSockets](https://dev.twitch.tv/docs/eventsub/handling-websocket-events/), [Webhooks](https://dev.twitch.tv/docs/eventsub/handling-webhook-events/), [Manage subscriptions](https://dev.twitch.tv/docs/eventsub/manage-subscriptions/), [Subscription types](https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/), [Chat auth](https://dev.twitch.tv/docs/chat/authenticating/), [Predictions reference](https://dev.twitch.tv/docs/api/predictions).

Verified facts:

- Authorization-code flow is the correct server flow. Redirect the browser to `https://id.twitch.tv/oauth2/authorize` with `response_type=code`, `client_id`, `redirect_uri`, URL-encoded space-delimited `scope`, and `state`. `force_verify` is optional. The callback receives `code` and `state`, or `error=access_denied`.
- Exchange `code` with `POST https://id.twitch.tv/oauth2/token` as `application/x-www-form-urlencoded`: `client_id`, `client_secret`, `code`, `grant_type=authorization_code`, `redirect_uri`. Success body includes `access_token`, `refresh_token`, `expires_in`, `scope`, and `token_type`. The sample `expires_in` is not a fixed lifetime. Store the returned value.
- `state` is how Twitch says to stop CSRF. Generate a unique random value per request and reject the callback when it does not match.
- Refresh is `POST https://id.twitch.tv/oauth2/token` with `grant_type=refresh_token`, `refresh_token` (URL-encoded), `client_id`, and `client_secret` for a confidential client. The refresh token can rotate. Invalid refresh returns `400` with message `Invalid refresh token`. A refresh can also return `401`. Only authorization-code user tokens are refreshable this way. App access tokens are not refreshable. Twitch’s guidance is to refresh after `401`, not on a timer derived from `expires_in`. A refresh token may have at most 50 live access tokens, so one worker must refresh per account.
- Confidential-client refresh tokens do not expire on a timer. Public-client refresh tokens expire 30 days after issue. Register a confidential app.
- Tokens also die when the user changes their password, Twitch revokes them, or the user disconnects the app at Twitch connection settings. Helix then returns `401`.
- Third-party apps that keep an OAuth session must call `GET https://id.twitch.tv/oauth2/validate` at startup and hourly. Header is `Authorization: OAuth <token>`; `Bearer` is also accepted. `200` returns `client_id`, `scopes`, `expires_in`, `login`, `user_id`. Invalid token returns `401` and `{"status":401,"message":"invalid access token"}`. On failure, end our session.
- Helix calls send `Authorization: Bearer <token>` and `Client-Id: <client id>`.
- Scopes for this MVP, taken from the endpoint and subscription pages:
  - `user:read:chat` for `channel.chat.message`.
  - `channel:manage:polls` for Create Poll and End Poll.
  - `channel:read:polls` or `channel:manage:polls` for Get Polls and for `channel.poll.begin`, `channel.poll.progress`, and `channel.poll.end`.
  - Request both poll scopes so the consent screen matches every call. Do not request `user:read:email`, `user:write:chat`, `user:bot`, `channel:bot`, or prediction scopes.
- `GET https://api.twitch.tv/helix/users` with a user token and no `id` or `login` returns the token’s user. `user:read:email` is required only for the email field. Do not request it. `view_count` is deprecated and must be ignored.
- `GET https://api.twitch.tv/helix/streams?user_id=<id>` accepts an app or user token. An offline channel is omitted from `data`. Useful fields: `id`, `user_id`, `user_login`, `user_name`, `game_id`, `game_name`, `type`, `title`, `viewer_count`, `started_at`, `language`. Empty `data` means not live, not an error.
- `GET https://api.twitch.tv/helix/channels?broadcaster_id=<id>` example response includes `title`, `game_id`, `game_name`, `broadcaster_language`, and `tags` even when presence in Get Streams is separate. The Authorization subsection was not cleanly extracted from the fetched reference markdown. Reconfirm on the live page before coding that call. Use it only to show the configured title and category while offline. Do not call Modify Channel Information.
- Create EventSub Subscription is `POST https://api.twitch.tv/helix/eventsub/subscriptions` and returns `202`. WebSocket transport requires a user access token and `transport.method=websocket` plus `transport.session_id`. An app token fails for WebSocket. Webhook transport requires an app access token, HTTPS callback on port 443, and a secret of 10 to 100 ASCII characters. Relevant errors: `400`, `401`, `403` missing scope, `409` duplicate type plus condition, `429`.
- WebSocket URL: `wss://eventsub.wss.twitch.tv/ws`. Optional `keepalive_timeout_seconds` is an integer from 10 to 600. First frame is `session_welcome` with `payload.session.id`. Subscribe within 10 seconds or the socket closes with `4003`. Messages: `notification`, `session_keepalive`, `session_reconnect`, `revocation`, then a close frame. Clients may send only Pong frames; other inbound traffic closes with `4001`. On `session_reconnect`, connect to `reconnect_url` unchanged, wait for welcome, then close the old socket. Subscriptions survive that reconnect. A dropped socket does not replay missed events and requires a new session plus new subscriptions. Limits per user token: 3 WebSocket connections with enabled subscriptions, 300 enabled subscriptions per connection, `max_total_cost` 10. Our four scoped subscriptions have documented cost 0, so the cost cap is not the binding limit.
- `channel.chat.message` version `1` condition is `broadcaster_user_id` and `user_id`. For this installed-app shape, both IDs are the connected broadcaster, and the token has `user:read:chat`. That matches the installed-chatbot path on the chat auth page. The event includes `message_id`, chatter identity, and `message.text`. We will not persist `message.text`. A live check that a broadcaster token actually receives their own chat is an acceptance test, not an assumption to skip.
- Poll events version `1` use condition `broadcaster_user_id` and require `channel:read:polls` or `channel:manage:polls`. Progress and end payloads include per-choice `votes`. End `status` in the official example is lowercase `completed`. Helix poll status values are uppercase: `ACTIVE`, `COMPLETED`, `TERMINATED`, `ARCHIVED`, `MODERATED`, `INVALID`. Our API will expose a lowercase enum and keep the raw Twitch status in the database.
- Create Poll: `POST https://api.twitch.tv/helix/polls`, scope `channel:manage:polls`, returns `200`. Body: `broadcaster_id` must be the token user, `title` max 60, `choices` 2 to 5 with each `title` max 25, `duration` 15 to 1800 seconds. The poll starts immediately. Only one poll may run at a time. `400` covers validation and “already running”. `401` covers token, scope, and broadcaster mismatch. Leave Channel Points voting off. Bits voting fields are documented as unused.
- Get Polls: `GET https://api.twitch.tv/helix/polls?broadcaster_id=<id>&id=<poll id>`. Scope `channel:read:polls` or `channel:manage:polls`. Polls remain available for 90 days. `ended_at` is null while `ACTIVE`.
- End Poll exists as `PATCH https://api.twitch.tv/helix/polls` with `status` `TERMINATED` or `ARCHIVED`. It is optional for the demo if the created poll is short. Include it only as a manual “end early” call if phase 7 finishes early. It is not required for the vertical slice.
- `stream.online` and `stream.offline` version `1` require no authorization. The subscription-management page also says that a WebSocket subscription for an event with no scope requirement must use a user access token that has no scopes. Our token will have scopes. Do not subscribe to those two types on that socket. Detect live status with Get Streams instead.
- Rate limit from the API guide: default bucket 800 points per minute. User-token calls are limited per client ID per user per minute. Response headers: `Ratelimit-Limit`, `Ratelimit-Remaining`, `Ratelimit-Reset` (Unix epoch). Excess returns `429`. Some endpoints can return `429` for other reasons, so read the body before assuming the bucket is empty.
- Webhook verification, documented and intentionally unused: HMAC-SHA256 of `message_id + timestamp + raw body`, prefixed `sha256=`, compared in constant time to `Twitch-Eventsub-Message-Signature`. The first webhook POST is `webhook_callback_verification` and the response body must be the raw `challenge`. WebSocket frames have no signature header. Authenticity for WebSocket comes from the connection we opened to Twitch’s host. Deduplicate with `metadata.message_id`.
- Predictions are real (`GET/POST https://api.twitch.tv/helix/predictions`, scopes `channel:read:predictions` or `channel:manage:predictions`, events `channel.prediction.*`) and are out of the MVP. They need a later resolve/cancel step and Channel Points, which is a worse demo than a poll.
- Send Chat Message is `POST https://api.twitch.tv/helix/chat/messages` and needs `user:write:chat`. Not in the MVP.

Transport decision: WebSocket only.

- WebSocket works on localhost, uses the user token we already have, and needs no public inbound port.
- Webhooks need a stable HTTPS port-443 callback, an app access token, challenge handling, signature checks, and retry behavior. That is the better long-running multi-instance design and the wrong amount of infrastructure for this deadline.
- Cost of the choice: one API replica, reconnect logic, and a gap in events if the socket drops. Record that gap on the listening session. Do not pretend missed events were received.

## 4. Architecture and component responsibilities

Modular monolith inside one FastAPI process.

- `api`: HTTP, status codes, cookie session, response models. No Twitch HTTP calls and no prompt text in route functions.
- `services`: OAuth completion, listening lifecycle, aggregation, suggestion creation, approval, poll refresh.
- `twitch`: httpx Helix client, token refresh, validate, WebSocket listener, payload parsers. Parses chat events down to counts and IDs before they leave the parser.
- `db`: SQLAlchemy models, session, repositories. Repositories are the only writers.
- `security`: Fernet token encryption, session-token hashing, OAuth state, log redaction.
- `engagement`: pure functions from buckets to the metrics document the model sees.
- Config: `pydantic-settings` from environment. Secrets never have defaults that look real.

In-process loops, started from FastAPI lifespan:

- WebSocket listener for each account with `listening_desired=true`.
- Get Streams snapshot every 30 seconds while listening.
- Validate each stored access token at startup and then hourly.
- Delete raw event receipts and chatter hashes older than 7 days, once per hour.

Single-flight refresh lock is an `asyncio.Lock` keyed by account ID in this process. That is sufficient because we will not run two replicas.

OpenAI client is called only from the suggestion service, with an 8-second timeout, temperature low, and a JSON schema limited to poll title, two to five choices, duration, and rationale. The prompt receives aggregates only. If the key is absent or the call fails schema validation, the rules fallback builds the same schema. Rules example: when `is_live` and `chat_messages` over the window is below a small threshold, propose a two-choice poll such as “What should we do next?” with duration 60. The rationale must describe counts and the latest viewer sample. It must not say retention, churn, or name a viewer.

## 5. Proposed directory structure

`backend/` is the service root. Paths below are relative to the repository root. Commands in later sections run from `backend/`.

```text
README.md
backend/README.md
backend/.env.example
backend/.gitignore
backend/Dockerfile
backend/docker-compose.yml
backend/pyproject.toml
backend/alembic.ini
backend/alembic/env.py
backend/alembic/versions/001_initial.py
backend/contracts/openapi.json
backend/contracts/examples/me.json
backend/contracts/examples/stream.json
backend/contracts/examples/metrics.json
backend/contracts/examples/suggestion.json
backend/contracts/examples/poll.json
backend/contracts/examples/error.json
backend/src/live_engagement_coach/main.py
backend/src/live_engagement_coach/config.py
backend/src/live_engagement_coach/api/errors.py
backend/src/live_engagement_coach/api/deps.py
backend/src/live_engagement_coach/api/v1/health.py
backend/src/live_engagement_coach/api/v1/auth.py
backend/src/live_engagement_coach/api/v1/stream.py
backend/src/live_engagement_coach/api/v1/engagement.py
backend/src/live_engagement_coach/api/v1/suggestions.py
backend/src/live_engagement_coach/api/v1/polls.py
backend/src/live_engagement_coach/db/base.py
backend/src/live_engagement_coach/db/session.py
backend/src/live_engagement_coach/db/models.py
backend/src/live_engagement_coach/db/repositories.py
backend/src/live_engagement_coach/security/crypto.py
backend/src/live_engagement_coach/security/sessions.py
backend/src/live_engagement_coach/twitch/client.py
backend/src/live_engagement_coach/twitch/oauth.py
backend/src/live_engagement_coach/twitch/eventsub.py
backend/src/live_engagement_coach/twitch/parsers.py
backend/src/live_engagement_coach/services/accounts.py
backend/src/live_engagement_coach/services/listening.py
backend/src/live_engagement_coach/services/metrics.py
backend/src/live_engagement_coach/services/suggestions.py
backend/src/live_engagement_coach/services/polls.py
backend/src/live_engagement_coach/services/rules.py
backend/tests/test_health.py
backend/tests/test_oauth_state.py
backend/tests/test_twitch_client.py
backend/tests/test_eventsub_dedup.py
backend/tests/test_poll_failures.py
backend/tests/test_suggestions_fallback.py
backend/tests/test_api_ownership.py
backend/tests/integration/test_demo_flow.py
```

The root [README.md](README.md) stays a short index: project name, one-paragraph description, and a pointer to `backend/README.md` for setup. It does not contain the Python project. `backend/contracts/openapi.json` is generated from the FastAPI app and committed. Hand-editing it is not the workflow.

## 6. Database schema

PostgreSQL 16. All timestamps are `timestamptz` in UTC. IDs are UUIDs except where the value is a Twitch ID stored as text.

- `twitch_accounts`: `id`, unique `twitch_user_id`, `login`, `display_name`, `access_token_ciphertext`, `refresh_token_ciphertext`, `token_expires_at`, `scopes` text array, `status` (`connected` or `needs_reauth`), `listening_desired` bool, `created_at`, `updated_at`. No email column.
- `oauth_states`: `state_hash` primary key, `expires_at`, `consumed_at`. Single use. TTL 10 minutes.
- `app_sessions`: `id`, `twitch_account_id` FK, unique `token_hash`, `expires_at`, `created_at`. Cookie stores the raw token. The database stores only its hash.
- `stream_snapshots`: `id`, `twitch_account_id` FK, nullable `twitch_stream_id`, `title`, `game_id`, `game_name`, `viewer_count` nullable, `started_at` nullable, `is_live`, `captured_at`. Index `(twitch_account_id, captured_at desc)`.
- `event_receipts`: `message_id` primary key, `twitch_account_id` FK, `subscription_type`, `message_timestamp`, `received_at`. This is the deduplication record. No chat body.
- `engagement_buckets`: `id`, `twitch_account_id` FK, `bucket_start` truncated to the minute, `chat_message_count`, `viewer_count_sample` nullable, `poll_votes_sample` nullable. Unique `(twitch_account_id, bucket_start)`.
- `chatter_presence`: `bucket_id` FK, `chatter_hash` (HMAC-SHA256 of Twitch chatter user ID with a server pepper). Unique `(bucket_id, chatter_hash)`. Raw chatter IDs are not stored. Login names are not stored.
- `listening_sessions`: `id`, `twitch_account_id` FK, `status` (`connecting`, `listening`, `degraded`, `stopped`), `websocket_session_id` nullable, `last_event_at` nullable, `last_gap_at` nullable, `started_at`, `stopped_at` nullable.
- `eventsub_subscriptions`: `id`, `listening_session_id` FK, `twitch_subscription_id`, `subscription_type`, `status`, `created_at`.
- `suggestions`: `id`, `twitch_account_id` FK, `status` (`proposed`, `approved`, `rejected`, `executed`, `failed`), `source` (`openai` or `rules`), `rationale`, `evidence` jsonb, `action_payload` jsonb, `created_at`, `decided_at` nullable, `failure_code` nullable. No exception strings.
- `polls`: `id`, `twitch_account_id` FK, `suggestion_id` FK unique, unique `twitch_poll_id`, `title`, `duration_seconds`, `twitch_status`, `started_at`, `ended_at` nullable, `created_at`.
- `poll_choices`: `id`, `poll_id` FK, `twitch_choice_id`, `title`, `votes`, `channel_points_votes`, `updated_at`. Unique `(poll_id, twitch_choice_id)`.

Direct from Twitch: viewer count, stream ID, title, category, started time, live presence, poll IDs, choice titles, vote totals, poll status.

Computed by us: messages per minute, unique chatters per window, minutes since the last counted message, and `chat_participation_ratio` = unique chatters divided by the latest non-null viewer sample. That ratio is a participation snapshot. It is not retention and not individual churn. There is no Twitch endpoint in this plan that returns chat volume, so chat counts exist only because we counted events.

Idempotency and recovery:

- Insert `event_receipts.message_id` first. A conflict means the frame was already applied. Chat has no separate timestamp in the verified payload, so the bucket minute is `metadata.message_timestamp`.
- Late frames still update the original minute. They are not dropped as out of order.
- Approving a suggestion checks `status=proposed` in the same transaction that sets `approved`, then calls Twitch. On success, status becomes `executed` and the poll row is inserted. On failure, status becomes `failed` with a safe code. A second approve returns `409`.
- Process restart: lifespan loads `listening_desired` accounts, opens a new socket, and subscribes again. Missed events during the gap are not backfilled. Set `last_gap_at`.
- Retention: delete `event_receipts` and `chatter_presence` older than 7 days. Keep snapshots, buckets, suggestions, and polls through the judging window. Polls on Twitch’s side remain readable for 90 days via Get Polls.

## 7. Frontend-facing API contract

Base path `/api/v1`. Cookie name `lec_session`, `HttpOnly`, `SameSite=Lax`, `Path=/`, `Secure` when `PUBLIC_BASE_URL` is HTTPS. CORS allows only `FRONTEND_ORIGIN` and `allow_credentials=true`.

Error body, used for every 4xx and 5xx. No token, secret, upstream body, or stack trace.

```json
{"error":{"code":"twitch_poll_already_active","message":"A poll is already running on this channel."}}
```

Auth: every route below requires the session cookie except health, Twitch start, and Twitch callback. Missing or dead session: `401` `unauthenticated`. Another account’s suggestion or poll ID: `404`, so existence does not leak.

`GET /api/v1/health` → `200`

```json
{"status":"ok"}
```

`GET /api/v1/auth/twitch/start` → `302` to `https://id.twitch.tv/oauth2/authorize`. No body.

`GET /api/v1/auth/twitch/callback` → `302` to `FRONTEND_SUCCESS_URL` and sets the cookie. `400` `invalid_oauth_state` or `access_denied`. `502` `token_exchange_failed`.

`POST /api/v1/auth/logout` → `204`. Deletes our session only. A Twitch revoke URL was not re-verified in this pass, so logout will not call Twitch.

`GET /api/v1/me` → `200`

```json
{"twitch_user_id":"141981764","login":"twitchdev","display_name":"TwitchDev","scopes":["user:read:chat","channel:manage:polls","channel:read:polls"],"status":"connected"}
```

`GET /api/v1/stream` → `200`. Refreshes from Twitch when the latest snapshot is older than 15 seconds. If Twitch is down and a snapshot exists, return it with `freshness` `stale` and `warning` `twitch_unavailable`. If none exists, `503` `twitch_unavailable`.

```json
{"is_live":true,"twitch_stream_id":"40952121085","title":"Just Chatting","game_name":"Just Chatting","viewer_count":18,"started_at":"2026-10-28T01:10:00Z","captured_at":"2026-10-28T01:40:00Z","freshness":"live"}
```

Offline example uses `"is_live":false`, `"twitch_stream_id":null`, `"viewer_count":null`.

`POST /api/v1/engagement/session/start` → `200` or `409` `already_listening`. `403` `missing_scope`. `502` `eventsub_unavailable`.

```json
{"status":"listening","subscriptions":["channel.chat.message","channel.poll.begin","channel.poll.progress","channel.poll.end"],"last_gap_at":null}
```

`POST /api/v1/engagement/session/stop` → `200` `{"status":"stopped"}`.

`GET /api/v1/engagement/session` → `200` with the same shape plus `last_event_at`.

`GET /api/v1/metrics?window_minutes=15` → `200`. Default 15. Allowed range 1 to 180. `400` `invalid_window` outside that range.

```json
{"window_minutes":15,"window_started_at":"2026-10-28T01:25:00Z","window_ended_at":"2026-10-28T01:40:00Z","chat_messages":4,"unique_chatters":2,"messages_per_minute":0.27,"latest_viewer_count":18,"chat_participation_ratio":0.11,"chat_participation_ratio_meaning":"unique chatters divided by the latest sampled viewer count; not retention or churn","minutes_since_last_message":3,"is_live":true,"event_gap":false}
```

`POST /api/v1/suggestions` → `201`. Always a proposal. Never a Twitch side effect.

```json
{"id":"6d1b5f3a-1c2e-4c3a-9f0e-2b7a9c0d1234","status":"proposed","source":"openai","rationale":"In the last 15 minutes there were 4 chat messages from 2 unique chatters while the latest viewer sample was 18. A one-minute poll gives people a way to participate without typing.","evidence":{"window_minutes":15,"chat_messages":4,"unique_chatters":2,"latest_viewer_count":18,"chat_participation_ratio":0.11,"is_live":true},"action":{"type":"create_poll","title":"What should we do next?","choices":["Boss fight","Viewer challenge"],"duration_seconds":60},"created_at":"2026-10-28T01:40:05Z"}
```

Rules fallback uses `"source":"rules"` and the same shape. `502` is not used for model failure.

`GET /api/v1/suggestions` and `GET /api/v1/suggestions/{id}` → `200`. Unknown ID → `404`.

`POST /api/v1/suggestions/{id}/reject` → `200` with `"status":"rejected"`. `409` `suggestion_not_pending` if it is not `proposed`.

`POST /api/v1/suggestions/{id}/approve` → `200` with the poll object below. `409` codes: `suggestion_not_pending`, `stream_offline`, `poll_already_active`. `401` if Twitch authorization is dead after refresh fails, with `needs_reauth`. `502` `twitch_poll_failed` for other Create Poll failures. `400` from our own validator if the stored payload breaks Twitch limits, which the suggestion service must prevent before insert.

`GET /api/v1/polls` → `200` `{"polls":[...]}`.

`GET /api/v1/polls/{id}` → `200`. If the stored Twitch status is `ACTIVE`, refresh from Get Polls first. If that refresh fails, return the last stored result with `"freshness":"stale"`.

```json
{"id":"9c0e2a11-7b3d-4e2f-8a55-11aa22bb33cc","suggestion_id":"6d1b5f3a-1c2e-4c3a-9f0e-2b7a9c0d1234","twitch_poll_id":"ed961efd-8a3f-4cf5-a9d0-e616c590cd2a","title":"What should we do next?","status":"active","twitch_status":"ACTIVE","duration_seconds":60,"started_at":"2026-10-28T01:41:00Z","ended_at":null,"freshness":"live","choices":[{"id":"4c123012-1351-4f33-84b7-43856e7a0f47","title":"Boss fight","votes":3,"channel_points_votes":0},{"id":"279087e3-54a7-467e-bcd0-c1393fcea4f0","title":"Viewer challenge","votes":5,"channel_points_votes":0}]}
```

Our `status` map: `active`, `completed`, `terminated`, `archived`, `moderated`, `invalid`.

Frontend workflow before the backend is finished: use `contracts/examples/*.json` and the committed OpenAPI document. FastAPI `/docs` and `/openapi.json` stay enabled. Each implementation phase regenerates `contracts/openapi.json`.

## 8. Security and privacy requirements

- `TWITCH_CLIENT_SECRET`, `TOKEN_ENCRYPTION_KEY`, `SESSION_PEPPER`, `CHATTER_HASH_PEPPER`, and `OPENAI_API_KEY` come from the environment. `backend/.env` is gitignored. `backend/.env.example` contains empty keys and comments only.
- Access and refresh tokens are Fernet-encrypted before insert. API responses and logs never include them. httpx logging redacts `Authorization` and token request bodies.
- OAuth `state` is 32 random bytes, stored as a hash, single use, 10-minute TTL. Mismatch or reuse stops the flow before the code is exchanged.
- Session token is 32 random bytes in an `HttpOnly` cookie. Database stores SHA-256 with `SESSION_PEPPER`. Session TTL 12 hours.
- Mutating requests check the session account and the row owner. Cookie `SameSite=Lax` plus a strict CORS origin is the CSRF control for this split frontend. The OAuth `state` value is the CSRF control for the Twitch redirect.
- Generic `500` `internal_error` for unexpected exceptions. Details stay in server logs with tokens already redacted.
- Do not store chat text, email, profile descriptions, or raw chatter IDs. Chatter identity used for unique counts is an HMAC.
- The model prompt is built from the metrics document only.
- Approve is the only route that calls Create Poll. Generation, rejection, metrics reads, and stream refresh cannot.
- One replica. Document that a second replica would split WebSocket state and could double-refresh tokens.

## 9. Implementation phases

Phase 0, human prerequisites, no code. Depends on nothing in the repo. Deliverable is a local `backend/.env` that is never committed. You create the empty `backend/` directory before implementation. Acceptance: Twitch app created, redirect URI copied exactly, client ID and secret available, OpenAI key available or an explicit decision to demo on rules only, Docker Desktop installed or Python 3.12 and PostgreSQL 16 installed.

Phase 1, skeleton and contract. Files, all under `backend/` except the root index: `backend/pyproject.toml`, `backend/Dockerfile`, `backend/docker-compose.yml`, `backend/.env.example`, `backend/.gitignore`, `backend/README.md`, root `README.md` pointer, `backend/src/live_engagement_coach/main.py`, `config.py`, `api/errors.py`, `api/v1/health.py`, `backend/tests/test_health.py`, `backend/contracts/examples/*.json`. Depends on phase 0 only for a full container run; the health unit test can run once Python 3.12 exists. Acceptance: from `backend/`, `GET /api/v1/health` returns `200`, `/openapi.json` includes the planned paths even if later handlers are still stubs that return `501` `not_implemented`, and example JSON files match section 7. No Python project files are created at the repo root.

Phase 2, schema. Files under `backend/`: `src/live_engagement_coach/db/base.py`, `db/session.py`, `db/models.py`, `alembic.ini`, `alembic/env.py`, `alembic/versions/001_initial.py`, `tests/integration/test_schema.py`. Depends on phase 1 and a Postgres URL. Acceptance: `alembic upgrade head` on an empty database creates every table and unique index in section 6, and a second upgrade is a no-op.

Phase 3, OAuth and session. Files under `backend/src/live_engagement_coach/` and `backend/tests/`: `security/crypto.py`, `security/sessions.py`, `twitch/oauth.py`, `api/deps.py`, `api/v1/auth.py`, `services/accounts.py`, `db/repositories.py`, `tests/test_oauth_state.py`. Depends on phases 1 and 2. Acceptance: mismatched, expired, and reused `state` never call the token endpoint; a mocked token response is stored as ciphertext that does not contain the raw token; callback sets the cookie; `/me` returns profile fields and `401` without the cookie.

Phase 4, Helix stream read and token maintenance. Files under `backend/`: `twitch/client.py`, `api/v1/stream.py`, `tests/test_twitch_client.py`. Depends on phase 3. Acceptance: mocked Get Users and Get Streams cover live, empty offline, `401` refresh-then-retry, failed refresh marking `needs_reauth`, and `429`. Logs of those tests do not contain the bearer token. Validate failure clears the session.

Phase 5, EventSub and aggregates. Files under `backend/`: `twitch/eventsub.py`, `twitch/parsers.py`, `services/listening.py`, `services/metrics.py`, `api/v1/engagement.py`, `tests/test_eventsub_dedup.py`. Depends on phase 4. Acceptance: a fake WebSocket welcome is followed by the four subscribe requests within the test’s time budget; a duplicate `message_id` does not increase the count; an older minute timestamp updates the older bucket; chat fixtures with text do not persist that text; metrics math matches a hand-computed fixture, including a null viewer count leaving the ratio null.

Phase 6, suggestions. Files under `backend/`: `services/suggestions.py`, `services/rules.py`, `api/v1/suggestions.py`, `tests/test_suggestions_fallback.py`. Depends on phase 5. Acceptance: mocked OpenAI JSON becomes a `proposed` row; a too-long title is rejected before insert; missing API key and HTTP failure each produce `source=rules`; the recorded prompt fixture contains counts and does not contain a message string or chatter ID; no test in this phase calls Create Poll.

Phase 7, approval and results. Files under `backend/`: `services/polls.py`, `api/v1/polls.py`, `tests/test_poll_failures.py`, `tests/integration/test_demo_flow.py`. Depends on phase 6. Acceptance: approve on a mocked Create Poll `200` stores the Twitch poll ID and choices; a second approve does not call Twitch; mocked `400` already-running becomes `409 poll_already_active`; offline approve does not call Twitch; a progress fixture updates votes; Get Polls refresh updates a completed poll. The integration test uses a real Postgres and mocked HTTP and WebSocket only.

Phase 8, judge-facing docs and demo script. Files: `backend/README.md` run steps, a short root `README.md` pointer, and `backend/docs/demo-script.md` for the video beats. Depends on phases 1 through 7. Acceptance: a newcomer can follow the root README into `backend/`, start Compose, open `/docs`, and run the service without reading source. `backend/README.md` states that the required Codex session ID comes from Codex `/status`, and that Cursor use is not that evidence.

## 10. Testing strategy

- Unit tests for metrics math, poll payload limits, OAuth state, error mapping, and the rules fallback. No network and no database.
- Twitch client tests with `pytest-httpx` or `respx` fixtures copied from the official response shapes for token exchange, refresh, validate, Get Users, Get Streams, Create EventSub Subscription, Create Poll, and Get Polls.
- OAuth tests assert the token endpoint is not called when `state` is missing, mismatched, expired, or already consumed, and when Twitch returns `access_denied`.
- WebSocket signature tests are not part of the suite because this transport has no `Twitch-Eventsub-Message-Signature`. Dedup tests cover duplicate `message_id`, a late frame for an earlier minute, and a revocation frame that marks the session `degraded`.
- Poll tests cover Create Poll `400` already-running, `401` after a failed refresh, and a success that is not repeated.
- Integration tests run against the Compose Postgres service. They drive the HTTP API through the demo sequence with mocked Twitch.
- No test, fixture, or CI job uses a live Twitch account or a live OpenAI key.
- Optional manual check, not part of CI: Twitch CLI mock EventSub server, then one live channel during the recorded demo.

## 11. Local setup and deployment plan

Compose file is `backend/docker-compose.yml`. Services: `api` on port 8000 built from `python:3.12-slim`, and `postgres:16` with a named volume. No Redis and no worker container. The API image runs `alembic upgrade head` then `uvicorn`. The build context is `backend/`, not the repo root.

Environment variables:

- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `TWITCH_REDIRECT_URI` default `http://localhost:8000/api/v1/auth/twitch/callback`
- `PUBLIC_BASE_URL` default `http://localhost:8000`
- `FRONTEND_ORIGIN` default `http://localhost:5173`
- `FRONTEND_SUCCESS_URL` default `http://localhost:5173/connected`
- `DATABASE_URL` `postgresql+asyncpg://coach:coach@postgres:5432/coach`
- `TOKEN_ENCRYPTION_KEY` a Fernet key
- `SESSION_PEPPER`
- `CHATTER_HASH_PEPPER`
- `OPENAI_API_KEY` optional
- `OPENAI_MODEL` required only when the key is set; choose the model at implementation time from the current OpenAI model list rather than freezing an ID in this plan
- `OPENAI_TIMEOUT_SECONDS` default `8`

Twitch console steps to document in `backend/README.md`: register a confidential application, set the OAuth redirect URI to the exact `TWITCH_REDIRECT_URI`, and put the client ID and secret in `backend/.env`. Localhost HTTP is the development callback. A deployed callback must be HTTPS and must be added in the console before it will work. WebSocket does not need a public inbound EventSub URL.

Host gap: this machine does not currently have Docker, and its Python is 3.11.0. Implementation should not silently target 3.11. Install Docker Desktop before the Compose acceptance check. If Docker cannot be installed, the fallback is Python 3.12 on the host plus a local PostgreSQL 16, with the same env vars and a README note. That fallback is a setup change, not a stack change.

Deployment for the video can be the presenter’s machine if the stream is live and the backend process stays up. A public host is optional. If used, it needs one replica, HTTPS for the frontend origin and OAuth redirect, the same env vars, and Postgres. Do not commit production secrets. Do not scale the API to two instances.

Local run, once prerequisites exist: `cd backend`, copy `.env.example` to `.env`, fill secrets, `docker compose up --build`, open `http://localhost:8000/docs`.

## 12. Risks, dependencies, and unresolved questions

- Docker and Python 3.12 are not on this machine. Phase 1’s container acceptance check is blocked until one of the setup paths in section 11 exists.
- A Twitch application does not exist yet. OAuth and the live demo cannot be recorded without it. Redirect URI mismatches fail at Twitch, not in our code.
- Broadcaster self-read of `channel.chat.message` is the documented installed-app condition, and it still needs one live confirmation. If Twitch rejects that subscribe, the MVP stops on chat events and the demo cannot show real participation counts. Do not invent a second bot account unless that confirmation fails and you approve the extra scopes `user:bot` and `channel:bot`.
- `stream.online` over WebSocket wants an unscoped user token, which conflicts with the scoped token this flow must request. Get Streams polling is the chosen substitute. Live and offline transitions can lag by up to the 30-second snapshot interval.
- EventSub does not replay frames lost during a disconnect. The UI must be allowed to show `event_gap`.
- Create Poll fails if any poll is already active on the channel, including one the streamer started in Twitch’s own dashboard.
- Whether Create Poll works while the channel is offline was not verified. The API will refuse that call.
- Get Channel Information’s authorization sentence needs a live re-read before that endpoint is coded. Get Streams is already sufficient for the live path.
- The OpenAI model ID and account quota are unresolved. The rules fallback must be good enough to finish the demo if the model is unavailable.
- Hackathon eligibility depends on the project being newly built inside the submission window. The current repo qualifies as an empty shell created inside that window. Adding older code would put that at risk.
- This plan was written in Cursor. The submission still needs a Codex session ID from the Codex thread that builds the project, a public YouTube video under three minutes, and a written description of features and Codex use. Private GitHub repos must be shared with the address given in the [rules](https://twitchcon-codex.devpost.com/rules).
- Logout does not revoke the Twitch grant, because that revoke endpoint was not re-verified here. The user can disconnect the app from Twitch settings. Our hourly validate call then ends the session.
- Predictions and chat sending were verified and deliberately left out.

## 13. Hackathon demo plan

Record under three minutes, public on YouTube, with both of these visible:

- The project running against a live Twitch channel: consent screen, listening status, a real chat message moving the metric, an on-screen suggestion that names those counts, an approval click, the poll appearing in Twitch chat or the channel poll UI, then vote totals back in our API or frontend.
- The project being built with Codex: the Codex thread and enough of the session to show Codex producing the backend. Run `/status` in that thread and copy the session ID into the Devpost form. Do not submit a Cursor session ID in its place.

Demo beats that fit the time limit:

- Channel already live on Just Chatting before the recording starts.
- Connect, start listening, send two or three chat lines from a second account.
- Generate, approve, and use a 60-second poll so the result can appear before the video ends.
- Cut once to the Codex session rather than narrating the whole history.

Repo deliverables before 2 Nov 2026 14:00 Pacific: source under `backend/`, root `README.md` pointing at `backend/README.md`, `backend/.env.example`, the description of features and Codex use, the Codex session ID, and the YouTube URL. Keep secrets out of the repo and out of the video.

## 14. Decisions requiring approval

Approve or correct these before implementation:

- Product scope is the poll vertical slice in section 2, with predictions, chat sending, follows, and webhooks excluded.
- EventSub transport is WebSocket only. Live status comes from Get Streams, not `stream.online`.
- OAuth scopes are only `user:read:chat`, `channel:manage:polls`, and `channel:read:polls`.
- Frontend auth is an `HttpOnly` session cookie, not a bearer token in browser storage.
- Chat text and raw chatter IDs are not stored. Unique chatters use an HMAC.
- AI cannot call Twitch. Approve is the only execution path. Missing OpenAI credentials fall back to rules.
- Offline channels cannot execute a poll.
- Stack is Python 3.12, FastAPI, Pydantic, PostgreSQL 16, SQLAlchemy 2, Alembic, httpx, pytest, and Docker Compose. No Redis or Celery.
- The service lives in `backend/`, which you will create. The root `README.md` stays a short index that points to `backend/README.md`. Backend setup steps, Compose, and `.env.example` are not placed at the repo root.
- Implementation that should count toward the Codex session requirement will be done in Codex, with the session ID captured from `/status`.
- Docker Desktop, a Twitch confidential app, and an OpenAI key or an explicit rules-only demo will be ready before the corresponding phases.
