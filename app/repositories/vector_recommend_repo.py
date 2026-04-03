# app/repositories/vector_recommend_repository.py

from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.character import Character
from app.models.tag import Tag
from app.models.user_behavior import UserBehavior


class VectorRecommendRepository:
    """向量推荐数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_tags(self) -> List[Tag]:
        """获取所有标签"""
        stmt = select(Tag).order_by(Tag.id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_all_categories(self) -> List[Category]:
        """获取所有类别"""

        stmt = select(Category).order_by(Category.id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_user_behaviors(self, user_id: int, days: int) -> List[UserBehavior]:
        """获取用户行为"""
        since = datetime.now() - timedelta(days=days)

        stmt = select(UserBehavior).where(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since
        ).options(
            selectinload(UserBehavior.character)
                .selectinload(Character.categories),
            selectinload(UserBehavior.character)
                .selectinload(Character.tags)
        ).order_by(UserBehavior.created_at.desc())

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_all_active_characters(self) -> List[Character]:
        """获取所有活跃角色"""
        stmt = select(Character).where(
            Character.is_active == True
        ).options(
            selectinload(Character.categories),
            selectinload(Character.tags)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_user_interacted_ids(self, user_id: int) -> List[int]:
        """获取用户互动过的角色ID"""
        stmt = select(UserBehavior.character_id).where(
            UserBehavior.user_id == user_id
        ).distinct()

        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]
