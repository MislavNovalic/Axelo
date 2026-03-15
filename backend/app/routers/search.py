"""
Global search — Cmd+K palette backend.
Searches issues (title, key, description) and projects (name, key).
Uses PostgreSQL ILIKE for simplicity; a GIN tsvector index can be added later.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.issue import Issue
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/")
def global_search(
    q: str = Query(..., min_length=1, max_length=128),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not q.strip():
        return {"issues": [], "projects": []}

    term = f"%{q.strip()}%"

    # Projects the user can access
    member_project_ids = {
        m.project_id
        for m in db.query(ProjectMember).filter_by(user_id=current_user.id).all()
    }
    accessible_projects = db.query(Project).filter(
        or_(Project.owner_id == current_user.id, Project.id.in_(member_project_ids))
    ).all()
    accessible_ids = [p.id for p in accessible_projects]

    # Search issues
    issues = (
        db.query(Issue)
        .filter(
            Issue.project_id.in_(accessible_ids),
            or_(
                Issue.title.ilike(term),
                Issue.key.ilike(term),
                Issue.description.ilike(term),
            ),
        )
        .limit(limit)
        .all()
    )

    # Search projects
    projects = (
        db.query(Project)
        .filter(
            Project.id.in_(accessible_ids),
            or_(Project.name.ilike(term), Project.key.ilike(term)),
        )
        .limit(10)
        .all()
    )

    return {
        "issues": [
            {
                "id":         i.id,
                "key":        i.key,
                "title":      i.title,
                "status":     i.status.value,
                "type":       i.type.value,
                "priority":   i.priority.value,
                "project_id": i.project_id,
            }
            for i in issues
        ],
        "projects": [
            {"id": p.id, "name": p.name, "key": p.key}
            for p in projects
        ],
    }
