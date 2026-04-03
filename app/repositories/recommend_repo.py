
from datetime import timedelta, datetime
from operator import and_
from typing import List

from sqlalchemy import select, func, and_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.character import Character
from app.models.user_behavior import UserBehavior, BehaviorType


class RecommendRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_hot_character(self, limit):
        stmt = select(Character).options(
            selectinload(Character.categories),
            selectinload(Character.tags)
        ).order_by(
            Character.popularity_score.desc()
        ).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_popular_characters(self, limit: int, hours: int) -> List[Character]:
        """
        获取近期流行角色
            这里选择的是根据各种行为的数量进行加权评分，近期行为越多的角色得分越高，从而排名靠前。
        """
        since = datetime.now() - timedelta(hours=hours)


        # 子查询：计算近期行为分数
        recent_scores = select(
            UserBehavior.character_id,
            func.sum(
                case(
                    (UserBehavior.behavior_type == BehaviorType.LIKE, 3),
                    (UserBehavior.behavior_type == BehaviorType.CHAT, 2),
                    (UserBehavior.behavior_type == BehaviorType.VIEW, 1),
                    else_=0
                )
            ).label('total_score')
        ).where(
            UserBehavior.created_at >= since
        ).group_by(
            UserBehavior.character_id
        ).subquery()

        # 按总分排序

        stmt = select(Character).join(
            recent_scores,
            Character.id == recent_scores.c.character_id
        ).options(
            selectinload(Character.categories),
            selectinload(Character.tags)
        ).where(
            Character.is_active == True
        ).order_by(
            desc(recent_scores.c.total_score)
        ).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_trending(self, limit: int, hours: int, min_interaction: int = 100
                        # 这两个权重，我感觉没必要有这个
                        # ,  growth_weight: float = 0.7,  volume_weight: float = 0.3
                        ) -> List[dict]:
        """
        这里是近期飙升
        利用角色增长率（用于计算飙升速度）
                这里的增长率是基于用户行为数据计算的，比较当前周期和上一周期的行为数量，来判断哪些角色在近期热度增长最快。
        """
        now = datetime.now()
        # 本期：最近 hours 小时 。current_start即为本期的开始时间
        current_start = now - timedelta(hours=hours)
        # 上期：再往前 hours 小时
        previous_start = current_start - timedelta(hours=hours)

        # 当前周期数据
        current = select(
            UserBehavior.character_id,
            func.count(UserBehavior.id).label('current_count')
        ).where(
            UserBehavior.created_at >= current_start
        ).group_by(
            UserBehavior.character_id
        ).subquery()

        # 上一周期数据
        previous = select(
            UserBehavior.character_id,
            func.count(UserBehavior.id).label('previous_count')
        ).where(
            and_(
                UserBehavior.created_at >= previous_start,
                UserBehavior.created_at < current_start
            )
        ).group_by(
            UserBehavior.character_id
        ).subquery()

        # 计算增长率
        stmt = select(
            Character,
            func.coalesce(current.c.current_count, 0).label('current'),
            func.coalesce(previous.c.previous_count, 0).label('previous')
        ).outerjoin(
            current, Character.id == current.c.character_id
        ).outerjoin(
            previous, Character.id == previous.c.character_id
        ).where(
            Character.is_active == True
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        growth_data = []
        for char, curr, prev in rows:
            # 过滤掉互动量太少的
            if curr < min_interaction:
                continue

            if prev == 0:
                # 上期为零，从无到有，给一个基础增长率
                # 可以根据 curr 大小给不同权重
                growth_rate = 100 + curr  # 基础值 + 当前量
            else:
                growth_rate = (curr - prev) / prev * 100  # 转为百分比

            growth_data.append({
                'character': char,
                'current': curr,
                'previous': prev,
                'growth_rate': round(growth_rate,2)
            })

        # 按增长率排序
        growth_data.sort(key=lambda x: x['growth_rate'], reverse=True)
        return growth_data[:limit]






