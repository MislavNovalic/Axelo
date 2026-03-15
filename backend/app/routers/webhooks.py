"""
Outbound webhooks router — Phase 3.
OWASP A01: admin/owner role required for all webhook management.
OWASP A10 (SSRF): URL validation enforced in webhook_delivery.py before every send.
"""
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import require_admin_or_owner
from app.core.webhook_delivery import deliver_event, ALLOWED_EVENTS
from app.models.user import User
from app.models.project import Project
from app.models.webhook import OutboundWebhook, WebhookDelivery

router = APIRouter(tags=["webhooks"])


class WebhookCreate(BaseModel):
    url: str = Field(..., max_length=2048)
    events: list[str] = Field(..., min_length=1)
    secret: Optional[str] = Field(None, max_length=256)   # auto-generated if omitted


class WebhookUpdate(BaseModel):
    url: Optional[str] = Field(None, max_length=2048)
    events: Optional[list[str]] = None
    active: Optional[bool] = None


def _project_or_404(project_id: int, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.get("/projects/{project_id}/webhooks")
def list_webhooks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _project_or_404(project_id, db)
    require_admin_or_owner(project, current_user, db)

    hooks = db.query(OutboundWebhook).filter(
        OutboundWebhook.project_id == project_id
    ).all()

    return [
        {
            "id": h.id,
            "url": h.url,
            "events": h.events,
            "active": h.active,
            "created_at": h.created_at.isoformat(),
        }
        for h in hooks
    ]


@router.post("/projects/{project_id}/webhooks", status_code=201)
def create_webhook(
    project_id: int,
    body: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _project_or_404(project_id, db)
    require_admin_or_owner(project, current_user, db)

    # Validate event names
    invalid = [e for e in body.events if e not in ALLOWED_EVENTS]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown events: {invalid}. Allowed: {sorted(ALLOWED_EVENTS)}",
        )

    # Max 10 webhooks per project
    count = db.query(OutboundWebhook).filter(
        OutboundWebhook.project_id == project_id
    ).count()
    if count >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 webhooks per project")

    hook = OutboundWebhook(
        project_id=project_id,
        url=body.url,
        secret=body.secret or secrets.token_hex(32),
        events=body.events,
    )
    db.add(hook)
    db.commit()
    db.refresh(hook)

    return {
        "id": hook.id,
        "url": hook.url,
        "secret": hook.secret,   # shown once at creation
        "events": hook.events,
        "active": hook.active,
        "created_at": hook.created_at.isoformat(),
    }


@router.patch("/projects/{project_id}/webhooks/{webhook_id}")
def update_webhook(
    project_id: int,
    webhook_id: int,
    body: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _project_or_404(project_id, db)
    require_admin_or_owner(project, current_user, db)

    hook = db.query(OutboundWebhook).filter(
        OutboundWebhook.id == webhook_id,
        OutboundWebhook.project_id == project_id,
    ).first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if body.url is not None:
        hook.url = body.url
    if body.events is not None:
        invalid = [e for e in body.events if e not in ALLOWED_EVENTS]
        if invalid:
            raise HTTPException(status_code=422, detail=f"Unknown events: {invalid}")
        hook.events = body.events
    if body.active is not None:
        hook.active = body.active

    db.commit()
    return {"id": hook.id, "url": hook.url, "events": hook.events, "active": hook.active}


@router.delete("/projects/{project_id}/webhooks/{webhook_id}", status_code=204)
def delete_webhook(
    project_id: int,
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _project_or_404(project_id, db)
    require_admin_or_owner(project, current_user, db)

    hook = db.query(OutboundWebhook).filter(
        OutboundWebhook.id == webhook_id,
        OutboundWebhook.project_id == project_id,
    ).first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(hook)
    db.commit()


@router.get("/projects/{project_id}/webhooks/{webhook_id}/deliveries")
def list_deliveries(
    project_id: int,
    webhook_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _project_or_404(project_id, db)
    require_admin_or_owner(project, current_user, db)

    hook = db.query(OutboundWebhook).filter(
        OutboundWebhook.id == webhook_id,
        OutboundWebhook.project_id == project_id,
    ).first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    deliveries = (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .offset(skip)
        .limit(min(limit, 50))
        .all()
    )

    return [
        {
            "id": d.id,
            "event": d.event,
            "status": d.status,
            "response_code": d.response_code,
            "attempts": d.attempts,
            "created_at": d.created_at.isoformat(),
        }
        for d in deliveries
    ]


@router.post("/projects/{project_id}/webhooks/{webhook_id}/test")
async def test_webhook(
    project_id: int,
    webhook_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a test ping delivery to verify the webhook endpoint."""
    project = _project_or_404(project_id, db)
    require_admin_or_owner(project, current_user, db)

    hook = db.query(OutboundWebhook).filter(
        OutboundWebhook.id == webhook_id,
        OutboundWebhook.project_id == project_id,
    ).first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    from app.core.webhook_delivery import _send_delivery
    from app.models.webhook import WebhookDelivery as _WD
    delivery = _WD(
        webhook_id=hook.id,
        event="ping",
        payload={"message": "Axelo webhook test ping", "project_id": project_id},
        status="pending",
        attempts=0,
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    background_tasks.add_task(_send_delivery, db, hook, delivery)
    return {"message": "Test ping queued", "delivery_id": delivery.id}
