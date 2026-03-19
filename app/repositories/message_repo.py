from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.message import Message
from app.schemas.message import MessageBase


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    async def create(self, conversation_id: int,
                     sender_type: str,
                     content: str,
                     token_count: int | None = None,
                     in_context: bool = True,
                     created_at :Optional[datetime] = None
                     ):
        if created_at is None:
            created_at = datetime.now()

        message = Message(conversation_id=conversation_id,
                          sender_type=sender_type,
                          content=content,
                          token_count=token_count,
                          in_context=in_context,
                          created_at=created_at)
        self.db.add(message)
        self.db.flush()  # 只 flush
        return message


    def get_message_count(self, conv_id):
        count = self.db.query(Message).filter(
            Message.conversation_id == conv_id
        ).count()
        return count

    def get_messages_page(self, conv_id, param):
        """逆序再逆序是因为获取历史消息都是从下到上的，而展示消息又是从上到下的"""
        messages = self.db.query(Message).filter(
            Message.conversation_id == conv_id
        ).order_by(Message.created_at.desc()) \
            .offset(param.offset) \
            .limit(param.limit) \
            .all()
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
