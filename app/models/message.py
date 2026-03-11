from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Boolean,
    Integer,
    ForeignKey,
    TIMESTAMP,
    func
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Message(Base):
    __tablename__ = "message"

    id = Column(BigInteger, primary_key=True, index=True)

    conversation_id = Column(
        BigInteger,
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # user / character / system
    sender_type = Column(String(20), nullable=False)

    content = Column(Text, nullable=False)

    # 是否参与上下文（裁剪用）
    in_context = Column(Boolean, nullable=False, default=True)

    token_count = Column(Integer)

    emotion = Column(String(20))

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    # ========== relationships ==========
    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )
