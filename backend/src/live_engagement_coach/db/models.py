import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TwitchAccount(Base):
    __tablename__ = "twitch_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twitch_user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    login: Mapped[str] = mapped_column(String)
    display_name: Mapped[str] = mapped_column(String)
    access_token_ciphertext: Mapped[str] = mapped_column(Text)
    refresh_token_ciphertext: Mapped[str] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String))
    status: Mapped[str] = mapped_column(String, default="connected")
    listening_desired: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OAuthState(Base):
    __tablename__ = "oauth_states"

    state_hash: Mapped[str] = mapped_column(String, primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AppSession(Base):
    __tablename__ = "app_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twitch_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("twitch_accounts.id"))
    token_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StreamSnapshot(Base):
    __tablename__ = "stream_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twitch_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("twitch_accounts.id"), index=True)
    twitch_stream_id: Mapped[str | None] = mapped_column(String)
    title: Mapped[str | None] = mapped_column(String)
    game_id: Mapped[str | None] = mapped_column(String)
    game_name: Mapped[str | None] = mapped_column(String)
    viewer_count: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_live: Mapped[bool] = mapped_column(Boolean)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventReceipt(Base):
    __tablename__ = "event_receipts"

    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    twitch_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("twitch_accounts.id"))
    subscription_type: Mapped[str] = mapped_column(String)
    message_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EngagementBucket(Base):
    __tablename__ = "engagement_buckets"
    __table_args__ = (UniqueConstraint("twitch_account_id", "bucket_start", name="uq_engagement_bucket"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twitch_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("twitch_accounts.id"), index=True)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    chat_message_count: Mapped[int] = mapped_column(Integer, default=0)
    viewer_count_sample: Mapped[int | None] = mapped_column(Integer)
    poll_votes_sample: Mapped[int | None] = mapped_column(Integer)
    chatters: Mapped[list["ChatterPresence"]] = relationship(back_populates="bucket")


class ChatterPresence(Base):
    __tablename__ = "chatter_presence"
    __table_args__ = (UniqueConstraint("bucket_id", "chatter_hash", name="uq_chatter_presence"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bucket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("engagement_buckets.id"))
    chatter_hash: Mapped[str] = mapped_column(String)
    bucket: Mapped[EngagementBucket] = relationship(back_populates="chatters")


class ListeningSession(Base):
    __tablename__ = "listening_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twitch_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("twitch_accounts.id"), index=True)
    status: Mapped[str] = mapped_column(String)
    websocket_session_id: Mapped[str | None] = mapped_column(String)
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_gap_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EventSubSubscription(Base):
    __tablename__ = "eventsub_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listening_session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("listening_sessions.id"))
    twitch_subscription_id: Mapped[str] = mapped_column(String)
    subscription_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twitch_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("twitch_accounts.id"), index=True)
    status: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    rationale: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSONB)
    action_payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String)


class Poll(Base):
    __tablename__ = "polls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twitch_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("twitch_accounts.id"), index=True)
    suggestion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suggestions.id"), unique=True)
    twitch_poll_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    twitch_status: Mapped[str] = mapped_column(String)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    choices: Mapped[list["PollChoice"]] = relationship(back_populates="poll")


class PollChoice(Base):
    __tablename__ = "poll_choices"
    __table_args__ = (UniqueConstraint("poll_id", "twitch_choice_id", name="uq_poll_choice"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poll_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("polls.id"))
    twitch_choice_id: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    votes: Mapped[int] = mapped_column(Integer, default=0)
    channel_points_votes: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    poll: Mapped[Poll] = relationship(back_populates="choices")
