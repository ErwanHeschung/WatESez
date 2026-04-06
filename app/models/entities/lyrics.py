import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from app.models.entities.base import Base

class Lyrics(Base):
    __tablename__ = "lyrics"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    fingerprint = Column(String, unique=True, index=True, nullable=False)
    language = Column(String(10))
    
    content = Column(JSONB, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())