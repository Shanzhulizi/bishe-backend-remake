from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.message_repo import MessageRepository


class MessageService:
    def __init__(self, db:AsyncSession):
        self.db = db
        self.message_repo = MessageRepository(db)
    async def get_history_messages_count(self, conv_id):
        total =await self.message_repo.get_message_count(conv_id)
        return total

    async def get_history_messages(self, conv_id, param):
        messages =await self.message_repo.get_messages_page(conv_id, param)

        return messages

    async def insert_greeting(self,conv_id,greeting):
        await self.message_repo.create(
            conversation_id=conv_id,
            sender_type="assistant",
            content=greeting,
            token_count=-1
        )
