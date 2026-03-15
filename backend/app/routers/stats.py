from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.issue import Issue, IssueStatus
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/dashboard")
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # projects this user belongs to
    membership_ids = [m.project_id for m in db.query(ProjectMember).filter_by(user_id=current_user.id).all()]
    project_ids = list(set(
        [p.id for p in db.query(Project).filter(Project.owner_id == current_user.id).all()] + membership_ids
    ))

    total_issues = db.query(Issue).filter(Issue.project_id.in_(project_ids)).count()
    open_issues  = db.query(Issue).filter(
        Issue.project_id.in_(project_ids),
        Issue.status.notin_([IssueStatus.done])
    ).count()
    done_issues  = db.query(Issue).filter(
        Issue.project_id.in_(project_ids),
        Issue.status == IssueStatus.done
    ).count()
    my_issues    = db.query(Issue).filter(
        Issue.project_id.in_(project_ids),
        Issue.assignee_id == current_user.id,
        Issue.status.notin_([IssueStatus.done])
    ).count()

    # unique team members across all projects
    all_member_ids = set(
        m.user_id for m in db.query(ProjectMember).filter(ProjectMember.project_id.in_(project_ids)).all()
    )

    # recent issues (last 10 updated)
    recent = db.query(Issue).filter(
        Issue.project_id.in_(project_ids),
        Issue.status != IssueStatus.backlog,
    ).order_by(Issue.id.desc()).limit(10).all()

    recent_out = [
        {
            "id": i.id, "key": i.key, "title": i.title,
            "status": i.status.value, "type": i.type.value,
            "priority": i.priority.value,
            "project_id": i.project_id,
            "assignee": {"full_name": i.assignee.full_name} if i.assignee else None,
        }
        for i in recent
    ]

    return {
        "total_projects": len(project_ids),
        "open_issues": open_issues,
        "done_issues": done_issues,
        "my_open_issues": my_issues,
        "total_members": len(all_member_ids),
        "recent_issues": recent_out,
    }
