from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.core.database import Base

class ModerationResult(Base):
    __tablename__ = "moderation_results"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    is_flagged = Column(Boolean, default=False)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
