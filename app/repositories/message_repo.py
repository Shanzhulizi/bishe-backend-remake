from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    async def create(self, conversation_id: int,
                     sender_type: str,
                     content: str,
                     token_count: int | None = None,
                     in_context: bool = True
):
        message = Message(conversation_id=conversation_id,
            sender_type=sender_type,
            content=content,
            token_count=token_count,
            in_context=in_context)
        self.db.add(message)
        await self.db.flush()  # 只 flush
        return message

    async def get_messages_by_conversation(
            self,
            conversation_id: int,
            limit: int = 20,
            order_by: str = "asc"
    ) -> list[Message]:
        stmt = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.in_context.is_(True)
        )

        if order_by == "asc":
            stmt = stmt.order_by(Message.created_at.asc())
        else:
            stmt = stmt.order_by(Message.created_at.desc())

        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

