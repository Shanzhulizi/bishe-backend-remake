# app/repositories/preference_repo.py

from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.character import Character
from app.models.tag import Tag
from app.models.user_behavior import UserBehavior


class PreferenceRepository:
    """用户偏好数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_recent_behaviors(self, user_id: int, days: int = 30, limit: int = 100) -> List[UserBehavior]:
        """
        获取用户最近的行为记录
        """
        since = datetime.now() - timedelta(days=days)

        stmt = select(UserBehavior).where(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since
        ).order_by(
            UserBehavior.created_at.desc()
        ).limit(limit).options(
            selectinload(UserBehavior.character)
                .selectinload(Character.categories),
            selectinload(UserBehavior.character)
                .selectinload(Character.tags)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_user_interacted_characters(self, user_id: int, limit: int = 50) -> List[int]:
        """
        获取用户互动过的角色ID（去重）
        """
        stmt = select(UserBehavior.character_id).where(
            UserBehavior.user_id == user_id
        ).distinct().limit(limit)

        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_characters_by_ids(self, character_ids: List[int]) -> List[Character]:
        """
        根据ID列表获取角色
        """
        if not character_ids:
            return []

        stmt = select(Character).options(
            selectinload(Character.categories),
            selectinload(Character.tags)
        ).where(
            Character.id.in_(character_ids),
            Character.is_active == True
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_recommendations_by_preferences(
            self,
            category_ids: List[int],
            tag_ids: List[int],
            exclude_ids: List[int],
            limit: int = 20
    ) -> List[Character]:
        """根据偏好推荐角色"""
        stmt = select(Character).options(
            selectinload(Character.categories),
            selectinload(Character.tags)
        ).where(
            Character.is_active == True,
            Character.id.notin_(exclude_ids)
        )

        # 优先匹配类别
        if category_ids:
            stmt = stmt.join(Character.categories).where(
                Category.id.in_(category_ids)
            )

        # 再匹配标签
        if tag_ids:
            stmt = stmt.join(Character.tags).where(
                Tag.id.in_(tag_ids)
            )

        stmt = stmt.order_by(Character.popularity_score.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()