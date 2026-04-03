from datetime import datetime, date
from typing import List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_behavior import UserBehavior


class BehaviorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_behavior(self, user_id: int, character_id: int, behavior_type: str):
        """获取用户行为"""
        # 获取今天的开始和结束时间
        today_start = datetime.combine(date.today(), datetime.min.time())  # 今天 00:00:00
        today_end = datetime.combine(date.today(), datetime.max.time())  # 今天 23:59:59.999999

        stmt = select(UserBehavior).where(
            UserBehavior.user_id == user_id,
            UserBehavior.character_id == character_id,
            UserBehavior.behavior_type == behavior_type,
            UserBehavior.created_at.between(today_start, today_end)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_like_record(self, user_id: int, character_id: int):
        """获取点赞记录"""
        stmt = select(UserBehavior).where(
            UserBehavior.user_id == user_id,
            UserBehavior.character_id == character_id,
            UserBehavior.behavior_type == 'LIKE'
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def record_view(self, user_id: int, character_id: int):
        """记录浏览"""
        behavior = UserBehavior(
            user_id=user_id,
            character_id=character_id,
            behavior_type='VIEW',
            created_at=datetime.now()
        )
        self.db.add(behavior)
        await self.db.flush()

    async def record_chat(self, user_id: int, character_id: int):
        """记录聊天"""
        behavior = UserBehavior(
            user_id=user_id,
            character_id=character_id,
            behavior_type='CHAT',
            created_at=datetime.now()
        )
        self.db.add(behavior)

        await self.db.flush()

    async def record_like(self, user_id: int, character_id: int):
        """记录点赞"""
        behavior = UserBehavior(
            user_id=user_id,
            character_id=character_id,
            behavior_type='LIKE',
            created_at=datetime.now()
        )
        self.db.add(behavior)
        await self.db.flush()

    async def delete_records(self, user_id, character_id, behavior_type):
        stmt = delete(UserBehavior).where(
            UserBehavior.user_id == user_id,
            UserBehavior.character_id == character_id,
            UserBehavior.behavior_type == behavior_type
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_views_count(self, character_id: int):
        """获取浏览次数"""
        stmt = select(UserBehavior).where(
            UserBehavior.character_id == character_id,
            UserBehavior.behavior_type == 'VIEW'
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def get_chats_count(self, character_id: int):
        """获取聊天次数"""
        stmt = select(UserBehavior).where(
            UserBehavior.character_id == character_id,
            UserBehavior.behavior_type == 'CHAT'
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def get_likes_count(self, character_id: int) -> int:
        """获取点赞次数"""
        stmt = select(UserBehavior).where(
            UserBehavior.character_id == character_id,
            UserBehavior.behavior_type == 'LIKE'
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def get_like_status(self, user_id: int, character_id: int) -> bool:
        """获取点赞状态"""
        stmt = select(UserBehavior).where(
            UserBehavior.character_id == character_id,
            UserBehavior.user_id == user_id,
            UserBehavior.behavior_type == 'LIKE'
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def batch_get_like_status(self, user_id: int, character_ids: List[int]) -> List:
        """批量获取点赞状态"""
        stmt = select(UserBehavior).where(
            UserBehavior.character_id.in_(character_ids),
            UserBehavior.user_id == user_id,
            UserBehavior.behavior_type == 'LIKE'
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
