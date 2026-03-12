from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class IssueType(str, enum.Enum):
    bug = "bug"
    story = "story"
    task = "task"
    epic = "epic"


class IssuePriority(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class IssueStatus(str, enum.Enum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    in_review = "in_review"
    done = "done"


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(IssueType), default=IssueType.task)
    status = Column(Enum(IssueStatus), default=IssueStatus.backlog)
    priority = Column(Enum(IssuePriority), default=IssuePriority.medium)
    story_points = Column(Integer, nullable=True)
    order = Column(Integer, default=0)
    due_date = Column(Date, nullable=True)  # ← new

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("issues.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="issues")
    sprint = relationship("Sprint", back_populates="issues")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_issues")
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reported_issues")
    comments = relationship("Comment", back_populates="issue", cascade="all, delete-orphan")
    children = relationship("Issue", foreign_keys=[parent_id])
    time_logs = relationship("TimeLog", back_populates="issue", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    body = Column(Text, nullable=False)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    issue = relationship("Issue", back_populates="comments")
    author = relationship("User", back_populates="comments")
