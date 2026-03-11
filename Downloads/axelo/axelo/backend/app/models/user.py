from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    memberships = relationship("ProjectMember", back_populates="user")
    assigned_issues = relationship("Issue", foreign_keys="Issue.assignee_id", back_populates="assignee")
    reported_issues = relationship("Issue", foreign_keys="Issue.reporter_id", back_populates="reporter")
    comments = relationship("Comment", back_populates="author")
