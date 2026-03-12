from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any


class NotificationOut(BaseModel):
    id: int
    type: str
    payload: dict[str, Any]
    link: Optional[str]
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
