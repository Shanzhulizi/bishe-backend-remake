from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.user_behavior import UserBehavior


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

    async def get_chat_count(self, user_id: int, character_id: int) -> int:
        """获取用户与某个角色的聊天消息数量"""
        stmt = select(func.count()).where(
            UserBehavior.character_id == character_id,
            UserBehavior.user_id == user_id,
            UserBehavior.behavior_type == 'chat'
        )

        result = self.db.execute(stmt)
        count = result.scalar()

        return count or 0

    def get_summary(self, user_id, character_id):
        # 先找到会话
        stmt_conversation = select(Conversation.id).where(
            Conversation.user_id == user_id,
            Conversation.character_id == character_id
        )
        result = self.db.execute(stmt_conversation)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None
        result = self.db.query(Conversation.summary).filter(
            Conversation.id == conversation.id
        ).first()

        return result[0] if result else None
    def get_summary_count(self, conversation_id):
        result = self.db.query(Conversation.summary_count).filter(
            Conversation.id == conversation_id
        ).first()
        return result[0] if result and result[0] else 0


    def save_summary(
            self,
            conversation_id: int,
            summary: str,
            summarized_count: int
    ) -> bool:
        """
        保存摘要
        """
        try:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
            ).first()

            if conversation:
                conversation.summary = summary
                conversation.summarized_count = summarized_count
                conversation.summary_updated_at = datetime.now()
                self.db.commit()

                return True
            else:

                return False
        except Exception as e:
            # logger.error(f"保存摘要失败: {e}")
            self.db.rollback()
            return False