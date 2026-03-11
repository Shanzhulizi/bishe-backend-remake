from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation


class ConversationRepository:

    @staticmethod
    async def get_active(
            db: Session,
            user_id: int,
            character_id: int
    ) -> Conversation | None:
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.character_id == character_id,
            Conversation.is_active.is_(True)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
            db: Session,
            user_id: int,
            character_id: int,
            title: str | None = None
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            character_id=character_id,
            title=title or "New Conversation",
            is_active=True
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    """
        这个啥意思？
        
    """

    @staticmethod
    async def touch(db: Session, conv: Conversation):
        conv.last_message_at = func.now()
