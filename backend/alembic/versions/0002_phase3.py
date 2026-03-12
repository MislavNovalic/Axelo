"""Phase 3: 2FA, OAuth, time tracking, outbound webhooks

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users: 2FA columns ────────────────────────────────────────────────────
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='users' AND column_name='totp_secret'
            ) THEN
                ALTER TABLE users
                    ADD COLUMN totp_secret VARCHAR(64),
                    ADD COLUMN totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                    ADD COLUMN totp_recovery_codes TEXT,
                    ADD COLUMN oauth_provider VARCHAR(32),
                    ADD COLUMN oauth_id VARCHAR(256);
                -- hashed_password becomes nullable for OAuth-only accounts
                ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;
            END IF;
        END$$;
    """)

    # ── time_logs table ───────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS time_logs (
            id          SERIAL PRIMARY KEY,
            issue_id    INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            minutes     INTEGER NOT NULL CHECK (minutes > 0),
            description VARCHAR(500),
            logged_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename='time_logs' AND indexname='ix_time_logs_issue'
            ) THEN
                CREATE INDEX ix_time_logs_issue ON time_logs(issue_id);
                CREATE INDEX ix_time_logs_user  ON time_logs(user_id);
            END IF;
        END$$;
    """)

    # ── outbound_webhooks table ───────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS outbound_webhooks (
            id          SERIAL PRIMARY KEY,
            project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            url         VARCHAR(2048) NOT NULL,
            secret      VARCHAR(256) NOT NULL,
            events      JSONB NOT NULL DEFAULT '[]'::jsonb,
            active      BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # ── webhook_deliveries table ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS webhook_deliveries (
            id             SERIAL PRIMARY KEY,
            webhook_id     INTEGER NOT NULL REFERENCES outbound_webhooks(id) ON DELETE CASCADE,
            event          VARCHAR(100) NOT NULL,
            payload        JSONB NOT NULL,
            status         VARCHAR(32) NOT NULL DEFAULT 'pending',
            response_code  INTEGER,
            response_body  TEXT,
            attempts       INTEGER NOT NULL DEFAULT 0,
            next_retry_at  TIMESTAMPTZ,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename='webhook_deliveries' AND indexname='ix_webhook_deliveries_webhook'
            ) THEN
                CREATE INDEX ix_webhook_deliveries_webhook ON webhook_deliveries(webhook_id, created_at DESC);
            END IF;
        END$$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS webhook_deliveries CASCADE;")
    op.execute("DROP TABLE IF EXISTS outbound_webhooks CASCADE;")
    op.execute("DROP TABLE IF EXISTS time_logs CASCADE;")
    op.execute("""
        ALTER TABLE users
            DROP COLUMN IF EXISTS totp_secret,
            DROP COLUMN IF EXISTS totp_enabled,
            DROP COLUMN IF EXISTS totp_recovery_codes,
            DROP COLUMN IF EXISTS oauth_provider,
            DROP COLUMN IF EXISTS oauth_id;
        ALTER TABLE users ALTER COLUMN hashed_password SET NOT NULL;
    """)
