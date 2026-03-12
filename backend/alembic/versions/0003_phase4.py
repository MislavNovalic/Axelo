"""Phase 4 — Orgs / multi-workspace + AI usage log + import jobs

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$ BEGIN

    -- ── Organisations ───────────────────────────────────────────────────────
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='organisations') THEN
        CREATE TABLE organisations (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(128) NOT NULL,
            slug        VARCHAR(64)  NOT NULL UNIQUE,
            logo_url    VARCHAR(512),
            plan        VARCHAR(32)  NOT NULL DEFAULT 'free',
            owner_id    INTEGER      NOT NULL REFERENCES users(id),
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_organisations_slug ON organisations(slug);
        CREATE INDEX ix_organisations_owner ON organisations(owner_id);
    END IF;

    -- ── Organisation memberships ─────────────────────────────────────────────
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='org_members') THEN
        CREATE TABLE org_members (
            id          SERIAL PRIMARY KEY,
            org_id      INTEGER NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role        VARCHAR(16) NOT NULL DEFAULT 'member',   -- owner|admin|member
            joined_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(org_id, user_id)
        );
        CREATE INDEX ix_org_members_org  ON org_members(org_id);
        CREATE INDEX ix_org_members_user ON org_members(user_id);
    END IF;

    -- ── Link projects → org (nullable for backwards compat) ─────────────────
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='projects' AND column_name='org_id'
    ) THEN
        ALTER TABLE projects ADD COLUMN org_id INTEGER REFERENCES organisations(id) ON DELETE SET NULL;
        CREATE INDEX ix_projects_org ON projects(org_id);
    END IF;

    -- ── AI usage log (rate-limit + audit trail) ──────────────────────────────
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='ai_usage_log') THEN
        CREATE TABLE ai_usage_log (
            id            SERIAL PRIMARY KEY,
            user_id       INTEGER NOT NULL REFERENCES users(id),
            project_id    INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            feature       VARCHAR(64) NOT NULL,   -- 'issue_summary' | 'sprint_plan'
            input_tokens  INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            latency_ms    INTEGER,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_ai_usage_user_day ON ai_usage_log(user_id, created_at);
        CREATE INDEX ix_ai_usage_project  ON ai_usage_log(project_id);
    END IF;

    -- ── Import jobs ──────────────────────────────────────────────────────────
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='import_jobs') THEN
        CREATE TABLE import_jobs (
            id            SERIAL PRIMARY KEY,
            project_id    INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            created_by    INTEGER NOT NULL REFERENCES users(id),
            source        VARCHAR(32) NOT NULL,   -- 'jira'|'linear'|'csv'|'axelo'
            status        VARCHAR(16) NOT NULL DEFAULT 'pending',
            total         INTEGER NOT NULL DEFAULT 0,
            imported      INTEGER NOT NULL DEFAULT 0,
            skipped       INTEGER NOT NULL DEFAULT 0,
            errors        JSONB,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            finished_at   TIMESTAMPTZ
        );
        CREATE INDEX ix_import_jobs_project ON import_jobs(project_id);
    END IF;

    END $$;
    """)


def downgrade():
    op.execute("""
        DROP TABLE IF EXISTS import_jobs;
        DROP TABLE IF EXISTS ai_usage_log;
        DROP TABLE IF EXISTS org_members;
        ALTER TABLE projects DROP COLUMN IF EXISTS org_id;
        DROP TABLE IF EXISTS organisations;
    """)
