"""
Custom Fields — P2.
Project admins define fields; issue values are stored as JSON.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class FieldType(str, enum.Enum):
    text    = "text"
    number  = "number"
    select  = "select"
    date    = "date"
    boolean = "boolean"


class CustomField(Base):
    __tablename__ = "custom_fields"

    id         = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name       = Column(String(64), nullable=False)
    field_type = Column(Enum(FieldType), nullable=False)
    options    = Column(JSON, nullable=True)    # for select: ["Option A", "Option B"]
    required   = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")


class CustomFieldValue(Base):
    __tablename__ = "custom_field_values"

    id       = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("custom_fields.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    value    = Column(JSON, nullable=True)      # stores text/number/date/bool as JSON

    field = relationship("CustomField")
