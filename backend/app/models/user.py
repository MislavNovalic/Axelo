from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True)   # nullable for OAuth-only accounts
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token_hash = Column(String(64), nullable=True, index=True)
    email_verification_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Phase 3 — 2FA
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False, nullable=False)
    totp_recovery_codes = Column(Text, nullable=True)   # JSON list of bcrypt-hashed codes

    # Phase 3 — OAuth / SSO
    oauth_provider = Column(String(32), nullable=True)  # "google" | "github" | None
    oauth_id = Column(String(256), nullable=True)        # provider's user ID

    memberships = relationship("ProjectMember", back_populates="user")
    assigned_issues = relationship("Issue", foreign_keys="Issue.assignee_id", back_populates="assignee")
    reported_issues = relationship("Issue", foreign_keys="Issue.reporter_id", back_populates="reporter")
    comments = relationship("Comment", back_populates="author")
    time_logs = relationship("TimeLog", back_populates="user")
