from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.issue import IssueType, IssuePriority


class IssueTemplate(Base):
    __tablename__ = "issue_templates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(IssueType), default=IssueType.task)
    priority = Column(Enum(IssuePriority), default=IssuePriority.medium)
    story_points = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
    created_by = relationship("User")
