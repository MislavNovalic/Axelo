import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember, MemberRole
from app.models.issue import Issue, Comment, IssueStatus
from app.models.notification import Notification
from app.schemas.issue import IssueCreate, IssueUpdate, IssueOut, IssueSummary, CommentCreate, CommentOut
from app.core.deps import get_current_user

logger = logging.getLogger("axelo.issues")
router = APIRouter(prefix="/api/projects/{project_id}/issues", tags=["issues"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_project_and_check_access(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ids = [m.user_id for m in project.members] + [project.owner_id]
    if user.id not in ids:
        logger.warning("Access denied: user=%d project=%d", user.id, project_id)
        raise HTTPException(status_code=403, detail="Access denied")
    return project


def _get_member_role(project: Project, user: User, db: Session) -> Optional[MemberRole]:
    member = db.query(ProjectMember).filter_by(project_id=project.id, user_id=user.id).first()
    return member.role if member else None


def _require_member_or_above(project: Project, user: User, db: Session):
    """A01 fix: Viewers are read-only — they cannot create/update/delete issues."""
    if project.owner_id == user.id:
        return
    role = _get_member_role(project, user, db)
    if role is None or role == MemberRole.viewer:
        logger.warning("Viewer attempted write: user=%d project=%d", user.id, project.id)
        raise HTTPException(status_code=403, detail="Viewers cannot modify issues")


async def _broadcast_and_notify(
    project_id: int,
    event: str,
    data: dict,
    actor_id: int,
    recipients: list,
    notif_type: str,
    notif_payload: dict,
    notif_link: str,
    db: Session,
):
    """Broadcast a WS event to the project and persist notifications for recipients."""
    from app.routers.websocket import manager
    await manager.broadcast_project(project_id, event, data, exclude_user=actor_id)
    for uid in recipients:
        if uid == actor_id:
            continue
        notif = Notification(
            user_id=uid,
            type=notif_type,
            payload=notif_payload,
            link=notif_link,
        )
        db.add(notif)
        await manager.send_to_user(uid, notif_type, notif_payload)
    db.commit()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[IssueSummary])
def list_issues(
    project_id: int,
    status: Optional[str] = None,
    sprint_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    response: Response = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    limit = min(limit, 200)
    _get_project_and_check_access(project_id, current_user, db)
    query = db.query(Issue).filter(Issue.project_id == project_id)
    if status:
        query = query.filter(Issue.status == status)
    if sprint_id is not None:
        query = query.filter(Issue.sprint_id == sprint_id)
    total = query.count()
    items = query.order_by(Issue.order).offset(offset).limit(limit).all()
    if response is not None:
        response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
async def create_issue(
    project_id: int,
    issue_in: IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_and_check_access(project_id, current_user, db)
    _require_member_or_above(project, current_user, db)

    count = db.query(Issue).filter(Issue.project_id == project_id).count()
    key = f"{project.key}-{count + 1}"
    issue = Issue(
        **issue_in.model_dump(),
        key=key,
        project_id=project_id,
        reporter_id=current_user.id,
        order=count,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    recipients = [issue.assignee_id] if issue.assignee_id else []
    await _broadcast_and_notify(
        project_id=project_id,
        event="issue.created",
        data={"id": issue.id, "key": issue.key, "title": issue.title, "status": issue.status},
        actor_id=current_user.id,
        recipients=recipients,
        notif_type="issue.assigned",
        notif_payload={"issue_key": issue.key, "issue_title": issue.title, "actor": current_user.full_name},
        notif_link=f"/projects/{project_id}/issues/{issue.id}",
        db=db,
    )
    return issue


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(
    project_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project_and_check_access(project_id, current_user, db)
    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.patch("/{issue_id}", response_model=IssueOut)
async def update_issue(
    project_id: int,
    issue_id: int,
    issue_in: IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_and_check_access(project_id, current_user, db)
    _require_member_or_above(project, current_user, db)

    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    old_status = issue.status
    old_assignee = issue.assignee_id
    update_data = issue_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(issue, field, value)

    # Burndown: track completion timestamp
    if "status" in update_data:
        if update_data["status"] == IssueStatus.done and old_status != IssueStatus.done:
            issue.completed_at = datetime.now(timezone.utc)
        elif update_data["status"] != IssueStatus.done:
            issue.completed_at = None

    db.commit()
    db.refresh(issue)

    recipients = []
    notif_type = "issue.updated"
    notif_payload = {"issue_key": issue.key, "issue_title": issue.title, "actor": current_user.full_name}

    if "assignee_id" in update_data and issue.assignee_id and issue.assignee_id != old_assignee:
        recipients = [issue.assignee_id]
        notif_type = "issue.assigned"
        notif_payload["message"] = f"{current_user.full_name} assigned you to {issue.key}"
    else:
        for uid in [issue.reporter_id, issue.assignee_id]:
            if uid and uid not in recipients:
                recipients.append(uid)

    await _broadcast_and_notify(
        project_id=project_id,
        event="issue.updated",
        data={"id": issue.id, "key": issue.key, "status": issue.status,
              "priority": issue.priority, "assignee_id": issue.assignee_id, "sprint_id": issue.sprint_id},
        actor_id=current_user.id,
        recipients=recipients,
        notif_type=notif_type,
        notif_payload=notif_payload,
        notif_link=f"/projects/{project_id}/issues/{issue.id}",
        db=db,
    )
    return issue


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(
    project_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_and_check_access(project_id, current_user, db)
    _require_member_or_above(project, current_user, db)

    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    issue_key = issue.key
    db.delete(issue)
    db.commit()

    from app.routers.websocket import manager
    await manager.broadcast_project(
        project_id, "issue.deleted",
        {"id": issue_id, "key": issue_key},
        exclude_user=current_user.id,
    )


@router.post("/{issue_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(
    project_id: int,
    issue_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_and_check_access(project_id, current_user, db)
    _require_member_or_above(project, current_user, db)

    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    comment = Comment(body=comment_in.body, issue_id=issue_id, author_id=current_user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    recipients = list({uid for uid in [issue.reporter_id, issue.assignee_id] if uid})
    await _broadcast_and_notify(
        project_id=project_id,
        event="comment.created",
        data={"issue_id": issue_id, "issue_key": issue.key, "comment_id": comment.id,
              "author": current_user.full_name, "body_preview": comment_in.body[:80]},
        actor_id=current_user.id,
        recipients=recipients,
        notif_type="comment.created",
        notif_payload={"issue_key": issue.key, "actor": current_user.full_name,
                       "body_preview": comment_in.body[:80]},
        notif_link=f"/projects/{project_id}/issues/{issue_id}",
        db=db,
    )
    return comment
