"""Initial schema + P1/P2 tables with GIN index for search

Revision ID: 0001
Revises:
Create Date: 2026-03-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All tables are created by create_all() on startup; this migration adds
    # the performance/security enhancements on top.

    # GIN index for full-text search on issues
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename='issues' AND indexname='ix_issues_fts'
            ) THEN
                CREATE INDEX ix_issues_fts ON issues
                USING GIN(to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,'')));
            END IF;
        END$$;
    """)

    # Index: notifications by user + read status (common query pattern)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename='notifications' AND indexname='ix_notifications_user_unread'
            ) THEN
                CREATE INDEX ix_notifications_user_unread
                ON notifications(user_id, read) WHERE read = false;
            END IF;
        END$$;
    """)

    # Index: audit_log by project + date
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename='audit_logs' AND indexname='ix_audit_log_project_date'
            ) THEN
                CREATE INDEX ix_audit_log_project_date
                ON audit_logs(project_id, created_at DESC);
            END IF;
        END$$;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_issues_fts")
    op.execute("DROP INDEX IF EXISTS ix_notifications_user_unread")
    op.execute("DROP INDEX IF EXISTS ix_audit_log_project_date")
