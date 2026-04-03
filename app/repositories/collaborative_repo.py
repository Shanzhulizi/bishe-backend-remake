# app/repositories/collaborative_repo.py
from datetime import datetime, timedelta
from typing import List, Tuple

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.character import Character
from app.models.user_behavior import UserBehavior


class CollaborativeRepository:
    """协同过滤数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_interacted_characters(self, user_id: int, days: int = 30) -> List[int]:
        """
        获取用户互动过的角色ID（带权重）
        """
        since = datetime.now() - timedelta(days=days)


        stmt = select(
            UserBehavior.character_id,
            func.count(UserBehavior.id).label('count')
        ).where(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since
        ).group_by(
            UserBehavior.character_id
        ).order_by(
            desc('count')
        ).limit(50)

        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    async def find_similar_users(
            self,
            user_id: int,
            user_characters: List[int],
            limit: int = 20
    ) -> List[Tuple[int, float]]:
        """
        找到相似用户（基于共同互动的角色）
        返回: [(user_id, 相似度分数)]
        """
        stmt = select(
            UserBehavior.user_id,
            func.count(UserBehavior.character_id).label('common_count')
        ).where(
            UserBehavior.character_id.in_(user_characters),
            UserBehavior.user_id != user_id
        ).group_by(
            UserBehavior.user_id
        ).order_by(
            desc('common_count')
        ).limit(limit)

        result = await self.db.execute(stmt)
        rows = result.all()

        total_chars = len(user_characters)
        return [(row[0], row[1] / total_chars) for row in rows]

    async def get_users_preferred_characters(
            self,
            user_ids: List[int],
            exclude_ids: List[int],
            limit: int = 20
    ) -> List[Character]:
        """
        获取这些用户喜欢的角色
        """
        # 统计这些用户最常互动的角色
        stmt = select(
            UserBehavior.character_id,
            func.count(UserBehavior.id).label('popularity')
        ).where(
            UserBehavior.user_id.in_(user_ids),
            ~UserBehavior.character_id.in_(exclude_ids)
        ).group_by(
            UserBehavior.character_id
        ).order_by(
            desc('popularity')
        ).limit(limit)

        result = await self.db.execute(stmt)
        char_ids = [row[0] for row in result.all()]

        if not char_ids:
            return []

        # 获取完整角色信息
        stmt = select(Character).options(
            selectinload(Character.categories),
            selectinload(Character.tags)
        ).where(
            Character.id.in_(char_ids),
            Character.is_active == True
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()