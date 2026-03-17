from enum import Enum as PyEnum

from sqlalchemy import Enum as SQLEnum


class BehaviorType(str, PyEnum):
    VIEW = "view"
    CHAT = "chat"
    LIKE = "like"



from sqlalchemy import Column, BigInteger, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base  # declarative_base


class UserBehavior(Base):
    __tablename__ = "user_behaviors"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(BigInteger, ForeignKey("character.id", ondelete="CASCADE"), nullable=False)
    # behavior_type = Column(String(20), nullable=False)  # 'view', 'chat', 'like', 'share'
    behavior_type = Column(SQLEnum(BehaviorType), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # 关联关系
    user = relationship("User", backref="behaviors")
    character = relationship("Character", backref="behaviors")

    def __repr__(self):
        return f"<UserBehavior(id={self.id}, user={self.user_id}, character={self.character_id}, type={self.behavior_type})>"