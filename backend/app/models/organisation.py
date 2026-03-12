"""Organisation / multi-workspace models — Phase 4."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Organisation(Base):
    __tablename__ = "organisations"

    id         = Column(Integer, primary_key=True)
    name       = Column(String(128), nullable=False)
    slug       = Column(String(64), nullable=False, unique=True)
    logo_url   = Column(String(512))
    plan       = Column(String(32), nullable=False, default="free")   # free|pro|enterprise
    owner_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner   = relationship("User", foreign_keys=[owner_id], lazy="select")
    members = relationship("OrgMember", back_populates="org", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="org", lazy="select")


class OrgMember(Base):
    __tablename__ = "org_members"
    __table_args__ = (UniqueConstraint("org_id", "user_id"),)

    id        = Column(Integer, primary_key=True)
    org_id    = Column(Integer, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False)
    user_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role      = Column(String(16), nullable=False, default="member")   # owner|admin|member
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    org  = relationship("Organisation", back_populates="members")
    user = relationship("User", lazy="select")


class AiUsageLog(Base):
    __tablename__ = "ai_usage_log"

    id            = Column(Integer, primary_key=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id    = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    feature       = Column(String(64), nullable=False)
    input_tokens  = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    latency_ms    = Column(Integer)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    user    = relationship("User", lazy="select")
    project = relationship("Project", lazy="select")


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id          = Column(Integer, primary_key=True)
    project_id  = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    source      = Column(String(32), nullable=False)   # jira|linear|csv|axelo
    status      = Column(String(16), nullable=False, default="pending")
    total       = Column(Integer, nullable=False, default=0)
    imported    = Column(Integer, nullable=False, default=0)
    skipped     = Column(Integer, nullable=False, default=0)
    errors      = Column("errors", String)             # JSON string of error list
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))

    project = relationship("Project", lazy="select")
    creator = relationship("User", lazy="select")
