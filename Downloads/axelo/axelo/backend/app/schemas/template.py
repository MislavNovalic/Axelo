from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.issue import IssueType, IssuePriority


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: IssueType = IssueType.task
    priority: IssuePriority = IssuePriority.medium
    story_points: Optional[int] = None


class TemplateOut(TemplateCreate):
    id: int
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True
