from sqlalchemy import Column, Integer, String, Boolean, JSON
from app.core.database import Base

class ModerationResult(Base):
    __tablename__ = "moderation_results"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    flagged = Column(Boolean, nullable=False)
    categories = Column(JSON, nullable=False)


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
