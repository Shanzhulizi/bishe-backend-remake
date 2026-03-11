from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    @staticmethod
    def get_by_username(db: Session, username: str) -> User:
        stmt = select(User).where(User.username == username)
        result = db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_id(db: Session, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = db.execute(stmt)
        return result.scalars().first()
