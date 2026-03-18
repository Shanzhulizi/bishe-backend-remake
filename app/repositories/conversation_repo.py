from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_active(
            self,
            user_id: int,
            character_id: int
    ) -> Optional[Conversation]:
        """获取活跃会话"""
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.character_id == character_id,
            Conversation.is_active.is_(True)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
            self,
            user_id: int,
            character_id: int,
            title: Optional[str] = None
    ) -> Conversation:
        """创建新会话"""
        conversation = Conversation(
            user_id=user_id,
            character_id=character_id,
            title=title or "New Conversation",
            is_active=True,
            last_message_at=func.now()  # 创建时也设置时间
        )
        self.db.add(conversation)
        self.db.flush()  # ✅ 改为 flush，不 commit
        return conversation

    async def touch(self, conv: Conversation) -> Conversation:
        """
        更新会话的最后消息时间

        当有新消息时调用，更新会话的 last_message_at 字段
        比如：用户发送消息后，AI回复后，都要更新这个时间
        """
        conv.last_message_at = func.now()
        self.db.add(conv)
        self.db.flush()  # ✅ 只 flush，不 commit
        return conv