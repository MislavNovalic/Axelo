from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base
from app.models.issue import IssueType, IssuePriority


class IssueTemplate(Base):
    __tablename__ = "issue_templates"

    id          = Column(Integer, primary_key=True, index=True)
    project_id  = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name        = Column(String(128), nullable=False)
    description = Column(String(512), nullable=True)  # template description shown in picker
    type        = Column(Enum(IssueType), default=IssueType.task)
    priority    = Column(Enum(IssuePriority), default=IssuePriority.medium)
    title_template  = Column(String(512), nullable=True)   # e.g. "[Bug] <short description>"
    body_template   = Column(Text, nullable=True)          # markdown body pre-fill
    default_labels  = Column(JSON, nullable=True)          # future-proofing
    created_by  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    project  = relationship("Project")
    creator  = relationship("User")
