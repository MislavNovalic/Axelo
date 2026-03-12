from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON
from app.database import Base


class OutboundWebhook(Base):
    __tablename__ = "outbound_webhooks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(2048), nullable=False)
    secret = Column(String(256), nullable=False)       # used for HMAC-SHA256 signing
    events = Column(JSON, nullable=False, default=list) # list of event strings
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
    deliveries = relationship("WebhookDelivery", back_populates="webhook",
                              cascade="all, delete-orphan",
                              order_by="WebhookDelivery.created_at.desc()")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("outbound_webhooks.id", ondelete="CASCADE"), nullable=False)
    event = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(32), default="pending")    # pending | success | failed
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempts = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    webhook = relationship("OutboundWebhook", back_populates="deliveries")
