from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type        = Column(String(64), nullable=False)   # assigned, commented, status_changed, added_to_project, sprint_started, sprint_completed, mentioned, role_changed
    title       = Column(String(255), nullable=False)
    body        = Column(Text, nullable=True)
    link        = Column(String(512), nullable=True)   # frontend route e.g. /projects/1/issues/5
    read        = Column(Boolean, default=False, nullable=False)
    actor_id    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id  = Column(Integer, nullable=True)
    issue_id    = Column(Integer, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user  = relationship("User", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id])
