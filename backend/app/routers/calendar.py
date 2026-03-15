from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.database import get_db
from app.models.user import User
from app.models.issue import Issue
from app.models.project import Project, ProjectMember
from app.schemas.issue import CalendarIssue, IssueUpdate
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/", response_model=List[CalendarIssue])
def get_my_calendar(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from calendar import monthrange
    last_day = monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, last_day)

    issues = (
        db.query(Issue)
        .filter(
            Issue.assignee_id == current_user.id,
            Issue.due_date >= start,
            Issue.due_date <= end,
        )
        .all()
    )

    result = []
    for issue in issues:
        project = db.query(Project).filter(Project.id == issue.project_id).first()
        result.append(CalendarIssue(
            id=issue.id,
            key=issue.key,
            title=issue.title,
            type=issue.type,
            status=issue.status,
            priority=issue.priority,
            due_date=issue.due_date,
            project_id=issue.project_id,
            project_key=project.key if project else "",
        ))
    return result


@router.patch("/{issue_id}/due-date")
def set_due_date(
    issue_id: int,
    body: IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A01 FIX: Verify user is a member of the issue's project before updating."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # IDOR fix: check project membership
    member = db.query(ProjectMember).filter_by(
        project_id=issue.project_id, user_id=current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    if body.due_date is not None:
        issue.due_date = body.due_date
        db.commit()
        db.refresh(issue)
    return {"ok": True}
