import asyncio
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.issue import Issue, Comment
from app.schemas.issue import IssueCreate, IssueUpdate, IssueOut, IssueSummary, CommentCreate, CommentOut
from app.core.deps import get_current_user
from app.core.ws_manager import manager
from app.core.notify import notify
from app.core.permissions import require_project_write, validate_assignee_is_member
from app.core.security import MAX_TITLE_LEN, MAX_DESC_LEN, MAX_COMMENT_LEN, clamp_str
from app.core.audit import audit

router = APIRouter(prefix="/api/projects/{project_id}/issues", tags=["issues"])


def get_project_and_check_access(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ids = {m.user_id for m in project.members} | {project.owner_id}
    if user.id not in ids:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


def _broadcast(project_id: int, event: str, data: dict, exclude_user_id: int | None = None):
    payload = {"event": event, "data": data}
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(manager.broadcast_to_project(project_id, payload, exclude_user_id))
        else:
            loop.run_until_complete(manager.broadcast_to_project(project_id, payload, exclude_user_id))
    except RuntimeError:
        asyncio.run(manager.broadcast_to_project(project_id, payload, exclude_user_id))


def _issue_summary(issue: Issue) -> dict:
    return {
        "id":          issue.id,
        "key":         issue.key,
        "title":       issue.title,
        "status":      issue.status.value,
        "priority":    issue.priority.value,
        "type":        issue.type.value,
        "assignee":    {"id": issue.assignee.id, "full_name": issue.assignee.full_name} if issue.assignee else None,
        "story_points": issue.story_points,
        "sprint_id":   issue.sprint_id,
        "order":       issue.order,
    }


# ── List ──────────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[IssueSummary])
def list_issues(
    project_id: int,
    status: Optional[str] = None,
    sprint_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_and_check_access(project_id, current_user, db)
    query = db.query(Issue).filter(Issue.project_id == project_id)
    if status:
        query = query.filter(Issue.status == status)
    if sprint_id is not None:
        query = query.filter(Issue.sprint_id == sprint_id)
    return query.order_by(Issue.order).offset(skip).limit(min(limit, 500)).all()


# ── Create ────────────────────────────────────────────────────────────────────
@router.post("/", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
def create_issue(
    project_id: int,
    issue_in: IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_and_check_access(project_id, current_user, db)
    # A01: Viewers cannot create
    require_project_write(project, current_user, db)
    # A01: Validate assignee is a project member
    validate_assignee_is_member(project, issue_in.assignee_id, db)

    count = db.query(Issue).filter(Issue.project_id == project_id).count()
    key = f"{project.key}-{count + 1}"

    data = issue_in.model_dump()
    data["title"] = clamp_str(data.get("title"), MAX_TITLE_LEN)
    data["description"] = clamp_str(data.get("description"), MAX_DESC_LEN)

    issue = Issue(**data, key=key, project_id=project_id, reporter_id=current_user.id, order=count)
    db.add(issue)
    db.commit()
    db.refresh(issue)

    audit(db, project_id, current_user.id, "issue", "created",
          entity_id=issue.id, entity_key=issue.key,
          description=f"Created issue {issue.key}: {issue.title}")
    db.commit()

    _broadcast(project_id, "issue_created", _issue_summary(issue), exclude_user_id=current_user.id)

    if issue.assignee_id and issue.assignee_id != current_user.id:
        notify(db, issue.assignee_id, type="assigned",
               title=f"You were assigned to {issue.key}", body=issue.title,
               link=f"/projects/{project_id}/issues/{issue.id}",
               actor_id=current_user.id, project_id=project_id, issue_id=issue.id)
        db.commit()

    return issue


# ── Get ───────────────────────────────────────────────────────────────────────
@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(project_id: int, issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_project_and_check_access(project_id, current_user, db)
    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


# ── Update ────────────────────────────────────────────────────────────────────
@router.patch("/{issue_id}", response_model=IssueOut)
def update_issue(
    project_id: int,
    issue_id: int,
    issue_in: IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_and_check_access(project_id, current_user, db)
    require_project_write(project, current_user, db)

    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    updates = issue_in.model_dump(exclude_unset=True)

    # A01: Validate new assignee is a project member
    if "assignee_id" in updates:
        validate_assignee_is_member(project, updates["assignee_id"], db)

    # Clamp lengths
    if "title" in updates:
        updates["title"] = clamp_str(updates["title"], MAX_TITLE_LEN)
    if "description" in updates:
        updates["description"] = clamp_str(updates["description"], MAX_DESC_LEN)

    old_assignee_id = issue.assignee_id
    old_status = issue.status.value

    diff = {k: [getattr(issue, k, None), v] for k, v in updates.items()
             if getattr(issue, k, None) != v}
    for field, value in updates.items():
        setattr(issue, field, value)
    db.commit()
    db.refresh(issue)

    if diff:
        audit(db, project_id, current_user.id, "issue", "updated",
              entity_id=issue.id, entity_key=issue.key, diff=diff,
              description=f"Updated {issue.key}")
        db.commit()

    _broadcast(project_id, "issue_updated", _issue_summary(issue), exclude_user_id=current_user.id)

    new_assignee_id = issue.assignee_id
    if "assignee_id" in updates and new_assignee_id and new_assignee_id != old_assignee_id and new_assignee_id != current_user.id:
        notify(db, new_assignee_id, type="assigned",
               title=f"You were assigned to {issue.key}", body=issue.title,
               link=f"/projects/{project_id}/issues/{issue.id}",
               actor_id=current_user.id, project_id=project_id, issue_id=issue.id)
        db.commit()

    if "status" in updates and issue.status.value != old_status:
        recipients = set()
        if issue.reporter_id and issue.reporter_id != current_user.id:
            recipients.add(issue.reporter_id)
        if issue.assignee_id and issue.assignee_id != current_user.id:
            recipients.add(issue.assignee_id)
        for uid in recipients:
            notify(db, uid, type="status_changed",
                   title=f"{issue.key} moved to {issue.status.value.replace('_', ' ').title()}",
                   body=issue.title, link=f"/projects/{project_id}/issues/{issue.id}",
                   actor_id=current_user.id, project_id=project_id, issue_id=issue.id)
        if recipients:
            db.commit()

    return issue


# ── Delete ────────────────────────────────────────────────────────────────────
@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(project_id: int, issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = get_project_and_check_access(project_id, current_user, db)
    require_project_write(project, current_user, db)
    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    iid = issue.id
    ikey = issue.key
    db.delete(issue)
    audit(db, project_id, current_user.id, "issue", "deleted",
          entity_id=iid, entity_key=ikey, description=f"Deleted issue {ikey}")
    db.commit()
    _broadcast(project_id, "issue_deleted", {"id": iid}, exclude_user_id=current_user.id)


# ── Comment ───────────────────────────────────────────────────────────────────
@router.post("/{issue_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    project_id: int,
    issue_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_and_check_access(project_id, current_user, db)
    require_project_write(project, current_user, db)

    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    body_text = clamp_str(comment_in.body, MAX_COMMENT_LEN)
    comment = Comment(body=body_text, issue_id=issue_id, author_id=current_user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    _broadcast(project_id, "comment_added", {
        "issue_id":    issue_id,
        "id":          comment.id,
        "body":        comment.body,
        "author_id":   current_user.id,
        "author_name": current_user.full_name,
        "created_at":  comment.created_at.isoformat() if comment.created_at else None,
    }, exclude_user_id=current_user.id)

    # @mention detection (limit match length to prevent ReDoS)
    mentioned = set()
    for name in re.findall(r'@([\w]{1,64}(?:\s[\w]{1,64})?)', body_text):
        u = db.query(User).filter(User.full_name.ilike(f"%{name.strip()}%")).first()
        if u and u.id != current_user.id:
            mentioned.add(u.id)

    recipients = set()
    if issue.reporter_id and issue.reporter_id != current_user.id:
        recipients.add(issue.reporter_id)
    if issue.assignee_id and issue.assignee_id != current_user.id:
        recipients.add(issue.assignee_id)

    for uid in recipients:
        notif_type  = "mentioned" if uid in mentioned else "commented"
        notif_title = (f"{current_user.full_name} mentioned you in {issue.key}"
                       if uid in mentioned
                       else f"{current_user.full_name} commented on {issue.key}")
        notify(db, uid, type=notif_type, title=notif_title, body=body_text[:120],
               link=f"/projects/{project_id}/issues/{issue.id}",
               actor_id=current_user.id, project_id=project_id, issue_id=issue.id)

    for uid in mentioned - recipients:
        notify(db, uid, type="mentioned",
               title=f"{current_user.full_name} mentioned you in {issue.key}",
               body=body_text[:120], link=f"/projects/{project_id}/issues/{issue.id}",
               actor_id=current_user.id, project_id=project_id, issue_id=issue.id)

    if recipients or mentioned:
        db.commit()

    return comment
