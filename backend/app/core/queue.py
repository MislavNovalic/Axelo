"""
Redis-backed async task queue using ARQ.

Architecture:
  - API enqueues jobs into Redis via `enqueue_email()`
  - The ARQ worker process (separate Docker service) picks them up and sends via SMTP
  - No email is ever lost on API restart — jobs persist in Redis

Worker is started with:
    arq app.core.queue.WorkerSettings
"""
import logging
from typing import Optional

from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings

logger = logging.getLogger(__name__)


# ── Redis connection settings ───────────────────────────────────────────────

def _redis_settings() -> RedisSettings:
    """Parse REDIS_URL into ARQ RedisSettings."""
    url = settings.REDIS_URL  # e.g. redis://redis:6379/0
    # arq accepts a RedisSettings object
    return RedisSettings.from_dsn(url)


# ── Task: send a notification email ────────────────────────────────────────

async def task_send_notification_email(
    ctx,                          # ARQ passes worker context as first arg
    *,
    notification_type: str,
    to_email: str,
    to_name: str,
    title: str,
    body: str,
    link: str = "",
    actor_name: str = "",
    project_name: str = "",
) -> None:
    """
    Async task executed by the ARQ worker.
    Dispatches to the correct email template based on notification_type.
    """
    from app.core.email import (
        send_assigned_email,
        send_mentioned_email,
        send_commented_email,
        send_sprint_started_email,
        send_sprint_completed_email,
        send_added_to_project_email,
        send_role_changed_email,
        send_generic_notification_email,
    )

    handlers = {
        "assigned":          send_assigned_email,
        "mentioned":         send_mentioned_email,
        "commented":         send_commented_email,
        "sprint_started":    send_sprint_started_email,
        "sprint_completed":  send_sprint_completed_email,
        "added_to_project":  send_added_to_project_email,
        "role_changed":      send_role_changed_email,
    }

    handler = handlers.get(notification_type, send_generic_notification_email)

    try:
        await handler(
            to_email=to_email,
            to_name=to_name,
            title=title,
            body=body,
            link=link,
            actor_name=actor_name,
            project_name=project_name,
        )
        logger.info(
            "Email notification sent: type=%s to=%s", notification_type, to_email
        )
    except Exception:
        logger.exception(
            "Failed to send email notification: type=%s to=%s", notification_type, to_email
        )
        raise  # ARQ will retry on failure


# ── Public helper — enqueue from API process ────────────────────────────────

async def enqueue_email(
    *,
    notification_type: str,
    to_email: str,
    to_name: str,
    title: str,
    body: str,
    link: str = "",
    actor_name: str = "",
    project_name: str = "",
) -> None:
    """
    Push an email job into the Redis queue.
    Call this from API route handlers / notify.py.
    Silently no-ops if Redis is unreachable (so API never breaks).
    """
    if not settings.EMAIL_NOTIFICATIONS_ENABLED:
        return
    if not settings.SMTP_HOST:
        return

    try:
        pool = await create_pool(_redis_settings())
        await pool.enqueue_job(
            "task_send_notification_email",
            notification_type=notification_type,
            to_email=to_email,
            to_name=to_name,
            title=title,
            body=body,
            link=link,
            actor_name=actor_name,
            project_name=project_name,
        )
        await pool.aclose()
    except Exception:
        logger.warning(
            "Could not enqueue email (Redis unavailable?): type=%s to=%s",
            notification_type, to_email,
        )


# ── ARQ WorkerSettings ──────────────────────────────────────────────────────

class WorkerSettings:
    """
    ARQ worker configuration.
    Start with: arq app.core.queue.WorkerSettings
    """
    functions = [task_send_notification_email]
    redis_settings = _redis_settings()
    max_jobs = 10
    job_timeout = 30          # seconds per job before timeout
    max_tries = 3             # retry failed jobs up to 3 times
    keep_result = 3600        # keep job result in Redis for 1 hour
