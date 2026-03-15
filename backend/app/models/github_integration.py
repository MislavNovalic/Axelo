"""GitHub Integration model — P2."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class GitHubIntegration(Base):
    __tablename__ = "github_integrations"

    id           = Column(Integer, primary_key=True, index=True)
    project_id   = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    repo_owner   = Column(String(128), nullable=False)
    repo_name    = Column(String(128), nullable=False)
    webhook_secret = Column(String(128), nullable=True)  # HMAC secret for event verification
    access_token = Column(String(512), nullable=True)    # encrypted in prod; plaintext here for simplicity
    created_by   = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")


class GitHubLink(Base):
    """Links a GitHub PR/commit to an Axelo issue."""
    __tablename__ = "github_links"

    id          = Column(Integer, primary_key=True, index=True)
    issue_id    = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    link_type   = Column(String(16), nullable=False)  # pr | commit
    gh_number   = Column(Integer, nullable=True)       # PR number
    gh_sha      = Column(String(64), nullable=True)    # commit SHA
    gh_title    = Column(String(512), nullable=True)
    gh_url      = Column(String(512), nullable=True)
    gh_state    = Column(String(32), nullable=True)    # open | closed | merged
    payload     = Column(JSON, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue")
