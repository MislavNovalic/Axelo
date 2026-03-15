"""
Roadmap / timeline router — Phase 3.
Returns epics and stories with date ranges for Gantt rendering.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.issue import Issue, IssueType, IssueStatus
from app.models.sprint import Sprint

router = APIRouter(tags=["roadmap"])


def _check_member(project: Project, user: User, db: Session):
    member = db.query(ProjectMember).filter_by(
        project_id=project.id, user_id=user.id
    ).first()
    if not member and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/projects/{project_id}/roadmap")
def get_roadmap(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns epics and their child stories with sprint date ranges
    for rendering a Gantt / timeline view.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _check_member(project, current_user, db)

    # All sprints for date reference
    sprints = {s.id: s for s in db.query(Sprint).filter(Sprint.project_id == project_id).all()}

    # Epics
    epics = (
        db.query(Issue)
        .filter(Issue.project_id == project_id, Issue.type == IssueType.epic)
        .order_by(Issue.order)
        .all()
    )

    # Stories / tasks (non-epic, excluding done for clutter)
    stories = (
        db.query(Issue)
        .filter(
            Issue.project_id == project_id,
            Issue.type.in_([IssueType.story, IssueType.task, IssueType.bug]),
        )
        .order_by(Issue.order)
        .all()
    )

    def _resolve_dates(issue: Issue):
        """Derive start/end from sprint dates or due_date."""
        start = end = None
        if issue.sprint_id and issue.sprint_id in sprints:
            sp = sprints[issue.sprint_id]
            start = sp.start_date.isoformat() if sp.start_date else None
            end = sp.end_date.isoformat() if sp.end_date else None
        if issue.due_date:
            end = issue.due_date.isoformat()
        return start, end

    def _fmt(issue: Issue):
        start, end = _resolve_dates(issue)
        return {
            "id": issue.id,
            "key": issue.key,
            "title": issue.title,
            "type": issue.type.value,
            "status": issue.status.value,
            "priority": issue.priority.value,
            "story_points": issue.story_points,
            "sprint_id": issue.sprint_id,
            "parent_id": issue.parent_id,
            "assignee_id": issue.assignee_id,
            "start_date": start,
            "end_date": end,
        }

    # Build tree: epic → children
    epic_map = {e.id: {**_fmt(e), "children": []} for e in epics}
    unparented = []

    for story in stories:
        s = _fmt(story)
        if story.parent_id and story.parent_id in epic_map:
            epic_map[story.parent_id]["children"].append(s)
        else:
            unparented.append(s)

    return {
        "epics": list(epic_map.values()),
        "unparented": unparented,
        "sprints": [
            {
                "id": sp.id,
                "name": sp.name,
                "status": sp.status.value,
                "start_date": sp.start_date.isoformat() if sp.start_date else None,
                "end_date": sp.end_date.isoformat() if sp.end_date else None,
            }
            for sp in sprints.values()
        ],
    }
