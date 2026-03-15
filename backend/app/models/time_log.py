from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TimeLog(Base):
    __tablename__ = "time_logs"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    minutes = Column(Integer, nullable=False)          # always positive
    description = Column(String(500), nullable=True)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue", back_populates="time_logs")
    user = relationship("User", back_populates="time_logs")
