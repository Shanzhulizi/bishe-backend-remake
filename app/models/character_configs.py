from sqlalchemy import Column, BigInteger, JSON, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class CharacterConfigs(Base):
    __tablename__ = "character_configs"

    character_id = Column(BigInteger, ForeignKey("character.id"), primary_key=True)
    persona = Column(JSON, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联 Character
    character = relationship("Character", back_populates="config")
