
from datetime import datetime

# models/character_usage.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint

from app.db.base import Base  # declarative_base


class CharacterLike(Base):
    """角色点赞记录"""
    __tablename__ = "character_likes"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("character.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)  # 改用 DateTime

    __table_args__ = (
        UniqueConstraint('character_id', 'user_id', name='unique_character_like'),
    )