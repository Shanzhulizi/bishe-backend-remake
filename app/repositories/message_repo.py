from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:

    @staticmethod
    async def create(
            db: Session,
            conversation_id: int,
            sender_type: str,
            content: str,
            token_count: int | None = None,
            in_context: bool = True

    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            content=content,
            token_count=token_count,
            in_context=in_context
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    async def get_messages_by_conversation(
            db: Session,
            conversation_id: int,
            limit: int = 20
    ) -> list[Message]:
        stmt = (
            select(Message)
                .where(
                Message.conversation_id == conversation_id,
                Message.in_context.is_(True)
            )
                .order_by(Message.created_at.desc())
                .limit(limit)
        )
        result = db.execute(stmt)
        return result.scalars().all()
