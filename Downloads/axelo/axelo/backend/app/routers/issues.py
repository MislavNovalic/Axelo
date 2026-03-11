from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.issue import Issue, Comment
from app.schemas.issue import IssueCreate, IssueUpdate, IssueOut, IssueSummary, CommentCreate, CommentOut
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/projects/{project_id}/issues", tags=["issues"])


def get_project_and_check_access(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ids = [m.user_id for m in project.members] + [project.owner_id]
    if user.id not in ids:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


@router.get("/", response_model=List[IssueSummary])
def list_issues(
    project_id: int,
    status: Optional[str] = None,
    sprint_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_and_check_access(project_id, current_user, db)
    query = db.query(Issue).filter(Issue.project_id == project_id)
    if status:
        query = query.filter(Issue.status == status)
    if sprint_id is not None:
        query = query.filter(Issue.sprint_id == sprint_id)
    return query.order_by(Issue.order).all()


@router.post("/", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
def create_issue(
    project_id: int,
    issue_in: IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_and_check_access(project_id, current_user, db)
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
    return issue


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(project_id: int, issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_project_and_check_access(project_id, current_user, db)
    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.patch("/{issue_id}", response_model=IssueOut)
def update_issue(
    project_id: int,
    issue_id: int,
    issue_in: IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_and_check_access(project_id, current_user, db)
    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    for field, value in issue_in.model_dump(exclude_unset=True).items():
        setattr(issue, field, value)
    db.commit()
    db.refresh(issue)
    return issue


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(project_id: int, issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_project_and_check_access(project_id, current_user, db)
    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    db.delete(issue)
    db.commit()


@router.post("/{issue_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    project_id: int,
    issue_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_and_check_access(project_id, current_user, db)
    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.project_id == project_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    comment = Comment(body=comment_in.body, issue_id=issue_id, author_id=current_user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
