from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.issue import Issue, Comment
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/")
def global_search(
    q: str = Query(..., min_length=1, max_length=200),
    project_id: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full-text search across issues, projects, and comments.

    Uses PostgreSQL ILIKE for case-insensitive substring matching.
    Results are scoped to projects the current user is a member of.
    Input is parameterized — no SQL injection risk (A03 fix).
    """
    limit = min(limit, 50)
    term = f"%{q}%"

    # Projects the user has access to
    member_project_ids = [
        m.project_id for m in
        db.query(ProjectMember).filter(ProjectMember.user_id == current_user.id).all()
    ]
    owned_ids = [
        p.id for p in
        db.query(Project).filter(Project.owner_id == current_user.id).all()
    ]
    accessible_project_ids = list(set(member_project_ids + owned_ids))

    project_filter = Project.id.in_(accessible_project_ids)
    if project_id:
        if project_id not in accessible_project_ids:
            return {"issues": [], "projects": [], "comments": []}
        issue_project_filter = Issue.project_id == project_id
        project_filter = Project.id == project_id
    else:
        issue_project_filter = Issue.project_id.in_(accessible_project_ids)

    # Search issues
    issues = (
        db.query(Issue)
        .filter(
            issue_project_filter,
            (Issue.title.ilike(term) | Issue.key.ilike(term) | Issue.description.ilike(term)),
        )
        .limit(limit)
        .all()
    )

    # Search projects
    projects = (
        db.query(Project)
        .filter(project_filter, (Project.name.ilike(term) | Project.key.ilike(term)))
        .limit(limit)
        .all()
    )

    # Search comments (via their issue's project)
    comments = (
        db.query(Comment)
        .join(Issue, Comment.issue_id == Issue.id)
        .filter(
            Issue.project_id.in_(accessible_project_ids) if not project_id
            else Issue.project_id == project_id,
            Comment.body.ilike(term),
        )
        .limit(limit)
        .all()
    )

    return {
        "issues": [
            {
                "id": i.id,
                "key": i.key,
                "title": i.title,
                "status": i.status,
                "type": i.type,
                "priority": i.priority,
                "project_id": i.project_id,
            }
            for i in issues
        ],
        "projects": [
            {"id": p.id, "name": p.name, "key": p.key}
            for p in projects
        ],
        "comments": [
            {
                "id": c.id,
                "body": c.body[:120],
                "issue_id": c.issue_id,
                "issue_key": c.issue.key if c.issue else None,
                "project_id": c.issue.project_id if c.issue else None,
            }
            for c in comments
        ],
    }
