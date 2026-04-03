from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_username(self, username: str) -> User:
        stmt = select(User).where(User.username == username)
        result =await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result =await self.db.execute(stmt)
        return result.scalars().first()
