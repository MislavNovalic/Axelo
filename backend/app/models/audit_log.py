from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, index=True)
    project_id  = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    entity_type = Column(String(32), nullable=False)   # issue | sprint | project | member | comment
    entity_id   = Column(Integer, nullable=True)
    entity_key  = Column(String(32), nullable=True)    # e.g. AX-12
    action      = Column(String(32), nullable=False)   # created | updated | deleted | status_changed | etc.
    diff        = Column(JSON, nullable=True)           # {"field": [old, new]}
    description = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user    = relationship("User")
    project = relationship("Project")
