"""initial

Revision ID: 001_initial
Revises: 
Create Date: 2026-10-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'twitch_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('twitch_user_id', sa.String(), nullable=False, unique=True),
        sa.Column('login', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('access_token_ciphertext', sa.Text(), nullable=False),
        sa.Column('refresh_token_ciphertext', sa.Text(), nullable=False),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='connected'),
        sa.Column('listening_desired', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_twitch_accounts_twitch_user_id', 'twitch_accounts', ['twitch_user_id'])

    op.create_table(
        'oauth_states',
        sa.Column('state_hash', sa.String(), primary_key=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'app_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('twitch_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('twitch_accounts.id'), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_app_sessions_token_hash', 'app_sessions', ['token_hash'])

    op.create_table(
        'stream_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('twitch_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('twitch_accounts.id'), nullable=False),
        sa.Column('twitch_stream_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('game_id', sa.String(), nullable=True),
        sa.Column('game_name', sa.String(), nullable=True),
        sa.Column('viewer_count', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_live', sa.Boolean(), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_stream_snapshots_twitch_account_id_captured_at', 'stream_snapshots', ['twitch_account_id', sa.text('captured_at DESC')])

    op.create_table(
        'event_receipts',
        sa.Column('message_id', sa.String(), primary_key=True),
        sa.Column('twitch_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('twitch_accounts.id'), nullable=False),
        sa.Column('subscription_type', sa.String(), nullable=False),
        sa.Column('message_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'engagement_buckets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('twitch_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('twitch_accounts.id'), nullable=False),
        sa.Column('bucket_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('chat_message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('viewer_count_sample', sa.Integer(), nullable=True),
        sa.Column('poll_votes_sample', sa.Integer(), nullable=True),
        sa.UniqueConstraint('twitch_account_id', 'bucket_start', name='uq_engagement_bucket'),
    )
    op.create_index('ix_engagement_buckets_twitch_account_id', 'engagement_buckets', ['twitch_account_id'])

    op.create_table(
        'chatter_presence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('bucket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagement_buckets.id'), nullable=False),
        sa.Column('chatter_hash', sa.String(), nullable=False),
        sa.UniqueConstraint('bucket_id', 'chatter_hash', name='uq_chatter_presence'),
    )

    op.create_table(
        'listening_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('twitch_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('twitch_accounts.id'), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('websocket_session_id', sa.String(), nullable=True),
        sa.Column('last_event_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_gap_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('stopped_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_listening_sessions_twitch_account_id', 'listening_sessions', ['twitch_account_id'])

    op.create_table(
        'eventsub_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listening_session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listening_sessions.id'), nullable=False),
        sa.Column('twitch_subscription_id', sa.String(), nullable=False),
        sa.Column('subscription_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'suggestions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('twitch_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('twitch_accounts.id'), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('evidence', postgresql.JSONB(), nullable=False),
        sa.Column('action_payload', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_code', sa.String(), nullable=True),
    )
    op.create_index('ix_suggestions_twitch_account_id', 'suggestions', ['twitch_account_id'])

    op.create_table(
        'polls',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('twitch_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('twitch_accounts.id'), nullable=False),
        sa.Column('suggestion_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suggestions.id'), nullable=False, unique=True),
        sa.Column('twitch_poll_id', sa.String(), nullable=False, unique=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('twitch_status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_polls_twitch_account_id', 'polls', ['twitch_account_id'])
    op.create_index('ix_polls_twitch_poll_id', 'polls', ['twitch_poll_id'])

    op.create_table(
        'poll_choices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('poll_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('polls.id'), nullable=False),
        sa.Column('twitch_choice_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('votes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('channel_points_votes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('poll_id', 'twitch_choice_id', name='uq_poll_choice'),
    )


def downgrade() -> None:
    op.drop_table('poll_choices')
    op.drop_table('polls')
    op.drop_table('suggestions')
    op.drop_table('eventsub_subscriptions')
    op.drop_table('listening_sessions')
    op.drop_table('chatter_presence')
    op.drop_table('engagement_buckets')
    op.drop_table('event_receipts')
    op.drop_table('stream_snapshots')
    op.drop_table('app_sessions')
    op.drop_table('oauth_states')
    op.drop_table('twitch_accounts')
