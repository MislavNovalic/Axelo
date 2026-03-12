"""Email verification columns on users table

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$ BEGIN

    -- email_verified flag (default False for new users, True for existing to avoid lockout)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='email_verified'
    ) THEN
        ALTER TABLE users
            ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN email_verification_token_hash VARCHAR(64),
            ADD COLUMN email_verification_expires_at TIMESTAMPTZ;

        -- Existing users are grandfathered as verified so they're not locked out
        UPDATE users SET email_verified = TRUE;

        CREATE INDEX ix_users_verification_token
            ON users(email_verification_token_hash)
            WHERE email_verification_token_hash IS NOT NULL;
    END IF;

    END $$;
    """)


def downgrade():
    op.execute("""
    ALTER TABLE users
        DROP COLUMN IF EXISTS email_verified,
        DROP COLUMN IF EXISTS email_verification_token_hash,
        DROP COLUMN IF EXISTS email_verification_expires_at;
    """)
