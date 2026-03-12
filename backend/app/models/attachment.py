from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id           = Column(Integer, primary_key=True, index=True)
    issue_id     = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    uploader_id  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    filename     = Column(String(255), nullable=False)
    stored_name  = Column(String(255), nullable=False)
    content_type = Column(String(128), nullable=True)
    size_bytes   = Column(BigInteger, default=0)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    uploader = relationship("User")
