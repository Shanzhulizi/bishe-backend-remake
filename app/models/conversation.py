from sqlalchemy import Column, BigInteger, String, Text, Boolean, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base  # declarative_base


class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(BigInteger, primary_key=True, index=True)

    user_id = Column(
        BigInteger,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    character_id = Column(
        BigInteger,
        ForeignKey("character.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    title = Column(String(100))
    is_active = Column(Boolean, nullable=False, default=True)

    # 长对话摘要（上下文压缩用）
    summary = Column(Text)

    last_message_at = Column(TIMESTAMP(timezone=True))

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # ========== relationships ==========
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
