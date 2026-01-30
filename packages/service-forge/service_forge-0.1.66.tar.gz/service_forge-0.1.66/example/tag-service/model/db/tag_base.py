import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from service_forge.db.trace_mixin import TraceMixin
from . import Base

class TagBase(Base, TraceMixin):
    __tablename__ = "tag"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    type = Column(String(50), nullable=True)
    user_id = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    example = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)