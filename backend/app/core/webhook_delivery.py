"""
Outbound webhook delivery service.
OWASP A10 (SSRF): validate URLs before delivery — blocks internal/loopback targets.
"""
import hmac
import json
import hashlib
import logging
import ipaddress
import socket
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.models.webhook import OutboundWebhook, WebhookDelivery

logger = logging.getLogger("axelo.webhooks")

# OWASP A10: block private / loopback IP ranges
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

ALLOWED_EVENTS = {
    "issue.created", "issue.updated", "issue.deleted",
    "sprint.started", "sprint.completed", "member.added",
}

RETRY_DELAYS = [60, 300, 1800]   # 1 min, 5 min, 30 min (seconds)
DELIVERY_TIMEOUT = 10             # seconds per request


def _is_safe_url(url: str) -> tuple[bool, str]:
    """Return (safe, reason). SSRF protection per OWASP A10."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Unparseable URL"

    if parsed.scheme not in ("http", "https"):
        return False, "Only http/https schemes allowed"

    host = parsed.hostname
    if not host:
        return False, "Missing hostname"

    # Block common internal hostnames
    if host.lower() in ("localhost", "metadata.google.internal", "169.254.169.254"):
        return False, "Internal hostname not allowed"

    # Resolve to IP and check against blocked ranges
    try:
        addr_info = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False, "Cannot resolve hostname"

    for info in addr_info:
        try:
            ip = ipaddress.ip_address(info[4][0])
            for net in _BLOCKED_NETWORKS:
                if ip in net:
                    return False, f"Resolved IP {ip} is in a private/reserved range"
        except ValueError:
            pass

    return True, ""


def _sign_payload(secret: str, body: bytes) -> str:
    """Return HMAC-SHA256 hex signature."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


async def deliver_event(db: Session, project_id: int, event: str, payload: dict[str, Any]) -> None:
    """
    Look up all active webhooks for the project subscribed to this event,
    create a delivery record, and send. Failures are queued for retry.
    Called from router mutators as a background task.
    """
    if event not in ALLOWED_EVENTS:
        logger.warning(f"Unknown webhook event: {event}")
        return

    hooks = (
        db.query(OutboundWebhook)
        .filter(
            OutboundWebhook.project_id == project_id,
            OutboundWebhook.active == True,
        )
        .all()
    )

    for hook in hooks:
        if event not in (hook.events or []):
            continue
        delivery = WebhookDelivery(
            webhook_id=hook.id,
            event=event,
            payload=payload,
            status="pending",
            attempts=0,
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        await _send_delivery(db, hook, delivery)


async def _send_delivery(db: Session, hook: OutboundWebhook, delivery: WebhookDelivery) -> None:
    body_dict = {
        "event": delivery.event,
        "delivery_id": delivery.id,
        "payload": delivery.payload,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    body_bytes = json.dumps(body_dict, default=str).encode("utf-8")
    sig = _sign_payload(hook.secret, body_bytes)

    safe, reason = _is_safe_url(hook.url)
    if not safe:
        logger.warning(f"Webhook {hook.id} blocked — SSRF: {reason}")
        delivery.status = "failed"
        delivery.response_body = f"Blocked: {reason}"
        db.commit()
        return

    delivery.attempts += 1
    try:
        async with httpx.AsyncClient(timeout=DELIVERY_TIMEOUT, follow_redirects=False) as client:
            resp = await client.post(
                hook.url,
                content=body_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Axelo-Event": delivery.event,
                    "X-Axelo-Signature-256": f"sha256={sig}",
                    "X-Axelo-Delivery": str(delivery.id),
                    "User-Agent": "Axelo-Webhooks/1.0",
                },
            )
        delivery.response_code = resp.status_code
        delivery.response_body = resp.text[:2000]
        if 200 <= resp.status_code < 300:
            delivery.status = "success"
            delivery.next_retry_at = None
        else:
            _schedule_retry(delivery)
    except Exception as exc:
        logger.error(f"Webhook {hook.id} delivery {delivery.id} error: {exc}")
        delivery.response_body = str(exc)[:500]
        _schedule_retry(delivery)

    db.commit()


def _schedule_retry(delivery: WebhookDelivery) -> None:
    """Set next retry time based on attempt count. After max retries → failed."""
    attempt_idx = delivery.attempts - 1
    if attempt_idx < len(RETRY_DELAYS):
        delay = RETRY_DELAYS[attempt_idx]
        delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        delivery.status = "pending"
    else:
        delivery.status = "failed"
        delivery.next_retry_at = None
