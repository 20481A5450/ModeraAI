from sqlalchemy import Column, Integer, Text, Boolean, DateTime, func
from app.core.database import Base  # Import after Base is defined

class ModerationResult(Base):
    __tablename__ = "moderation_results"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    is_flagged = Column(Boolean, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ModerationResultBase(BaseModel):
    content: str
    flagged: bool
    reason: Optional[str] = None

class ModerationResultCreate(ModerationResultBase):
    pass

class ModerationResultResponse(ModerationResultBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
