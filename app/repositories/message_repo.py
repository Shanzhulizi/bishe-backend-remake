from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.schemas.message import MessageBase


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, conversation_id: int,
                     sender_type: str,
                     content: str,
                     token_count: int | None = None,
                     in_context: bool = True,
                     created_at: Optional[datetime] = None
                     ) -> Message:
        if created_at is None:
            created_at = datetime.now()

        message = Message(conversation_id=conversation_id,
                          sender_type=sender_type,
                          content=content,
                          token_count=token_count,
                          in_context=in_context,
                          created_at=created_at)
        self.db.add(message)
        await self.db.flush()  # 只 flush
        return message

    async def get_message_count(self, conv_id):
        """获取消息总数"""
        stmt = select(func.count()).select_from(Message).where(
            Message.conversation_id == conv_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def get_messages_page(self, conv_id, param):
        """逆序再逆序是因为获取历史消息都是从下到上的，而展示消息又是从上到下的"""
        stmt = select(Message).where(
            Message.conversation_id == conv_id
        ).order_by(desc(Message.created_at)).offset(param.offset).limit(param.limit)

        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        history = [
            MessageBase(
                sender_type=msg.sender_type,
                content=msg.content,
                token_count=msg.token_count,
                in_context=msg.in_context
            )
            for msg in messages
        ]
        return history[::-1]  # 反转列表
