from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.sprint import SprintStatus
from app.schemas.issue import IssueSummary


class SprintBase(BaseModel):
    name: str
    goal: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SprintCreate(SprintBase):
    pass


class SprintUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[SprintStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SprintOut(SprintBase):
    id: int
    status: SprintStatus
    project_id: int
    issues: List[IssueSummary] = []
    created_at: datetime

    class Config:
        from_attributes = True
