from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.conversation import Conversation
from app.models.message import Message

logger = get_logger(__name__)


class ConversationRepository:
    def __init__(self, db: AsyncSession):
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
            Conversation.is_active == True
        ).order_by(Conversation.last_message_at.desc()).limit(1)

        result = await self.db.execute(stmt)
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
        await self.db.flush()
        return conversation

    async def touch(self, conv: Conversation) -> Conversation:
        """
        更新会话的最后消息时间

        当有新消息时调用，更新会话的 last_message_at 字段
        比如：用户发送消息后，AI回复后，都要更新这个时间
        """
        conv.last_message_at = func.now()
        self.db.add(conv)
        await self.db.flush()
        return conv

    # repositories/conversation_repo.py

    async def get_summary(self, conversation_id: int) -> Optional[str]:
        """获取会话摘要"""
        try:
            stmt = select(Conversation.summary).where(
                Conversation.id == conversation_id
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取摘要失败: {e}")
            return None

    async def get_summary_count(self, conversation_id: int) -> int:
        """获取已总结的消息数量"""
        try:
            stmt = select(Conversation.summary_count).where(
                Conversation.id == conversation_id
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() or 0
        except Exception as e:
            logger.error(f"获取总结数量失败: {e}")
            return 0

    async def get_chat_count(self, conversation_id: int) -> int:
        """获取会话的消息总数"""
        try:
            stmt = select(func.count()).select_from(Message).where(
                Message.conversation_id == conversation_id
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() or 0
        except Exception as e:
            logger.error(f"获取消息数量失败: {e}")
            return 0

    async def save_summary(self, conversation_id: int, summary: str, summary_count: int) -> bool:
        """保存摘要"""
        try:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await self.db.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation:
                conversation.summary = summary
                conversation.summary_count = summary_count
                conversation.summary_updated_at = datetime.now()
                self.db.add(conversation)
                await self.db.commit()
                logger.info(f"保存摘要成功: conversation_id={conversation_id}, summarized_count={summary_count}")
                return True
            else:
                logger.error(f"会话不存在: {conversation_id}")
                return False
        except Exception as e:
            logger.error(f"保存摘要失败: {e}")
            await self.db.rollback()
            return False
