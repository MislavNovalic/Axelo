from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from app.models.issue import IssueType, IssueStatus, IssuePriority
from app.schemas.user import UserOut


class CommentBase(BaseModel):
    body: str


class CommentCreate(CommentBase):
    pass


class CommentOut(CommentBase):
    id: int
    author: UserOut
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class IssueBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: IssueType = IssueType.task
    status: IssueStatus = IssueStatus.backlog
    priority: IssuePriority = IssuePriority.medium
    story_points: Optional[int] = None
    assignee_id: Optional[int] = None
    sprint_id: Optional[int] = None
    parent_id: Optional[int] = None


class IssueCreate(IssueBase):
    pass


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[IssueType] = None
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    story_points: Optional[int] = None
    assignee_id: Optional[int] = None
    sprint_id: Optional[int] = None
    order: Optional[int] = None
    due_date: Optional[date] = None


class IssueOut(IssueBase):
    id: int
    key: str
    order: int
    project_id: int
    reporter: UserOut
    assignee: Optional[UserOut]
    comments: List[CommentOut] = []
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class IssueSummary(BaseModel):
    id: int
    key: str
    title: str
    type: IssueType
    status: IssueStatus
    priority: IssuePriority
    story_points: Optional[int]
    order: int
    sprint_id: Optional[int]
    assignee: Optional[UserOut]

    class Config:
        from_attributes = True


# ── Calendar ──────────────────────────────────────────────────────────────────
from datetime import date as DateType

class CalendarIssue(BaseModel):
    id: int
    key: str
    title: str
    type: IssueType
    status: IssueStatus
    priority: IssuePriority
    due_date: DateType
    project_id: int
    project_key: str = ""

    class Config:
        from_attributes = True
