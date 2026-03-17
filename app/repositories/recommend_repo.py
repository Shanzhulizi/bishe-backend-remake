# app/services/hot_recommend_service.py
from datetime import timedelta, datetime
from operator import and_, or_
from typing import List, Optional
from sqlalchemy import case

from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload

from app.models.character import Character
from app.models.user_behavior import UserBehavior, BehaviorType


class RecommendRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_hot_character(self, limit):
        result = self.db.query(Character).options(
            joinedload(Character.categories),  # 预加载关联
            joinedload(Character.tags)
        ).order_by(
            Character.popularity_score.desc()
        ).limit(limit).all()

        return result

    def get_popular_characters(self, limit: int, hours: int) -> List[Character]:
        """
        获取近期流行角色
            这里选择的是根据各种行为的数量进行加权评分，近期行为越多的角色得分越高，从而排名靠前。
        """
        since = datetime.now() - timedelta(hours=hours)

        # 使用 CASE WHEN 给不同行为赋权重
        recent_scores = self.db.query(
            UserBehavior.character_id,
            func.sum(
                case(
                    (UserBehavior.behavior_type == BehaviorType.LIKE, 3),
                    (UserBehavior.behavior_type == BehaviorType.CHAT, 2),
                    (UserBehavior.behavior_type == BehaviorType.VIEW, 1),
                    else_=0
                )
            ).label('total_score')
        ).filter(
            UserBehavior.created_at >= since
        ).group_by(
            UserBehavior.character_id
        ).subquery()

        # 按总分排序
        return self.db.query(Character).join(
            recent_scores,
            Character.id == recent_scores.c.character_id
        ).options(
            joinedload(Character.categories),
            joinedload(Character.tags)
        ).filter(
            Character.is_active == True
        ).order_by(
            desc(recent_scores.c.total_score)
        ).limit(limit).all()

    def get_trending(self, limit: int, hours: int, min_interaction: int = 100
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
        current = self.db.query(
            UserBehavior.character_id,
            func.count(UserBehavior.id).label('current_count')
        ).filter(
            UserBehavior.created_at >= current_start
        ).group_by(
            UserBehavior.character_id
        ).subquery()

        # 上一周期数据
        previous = self.db.query(
            UserBehavior.character_id,
            func.count(UserBehavior.id).label('previous_count')
        ).filter(
            and_(
                UserBehavior.created_at >= previous_start,
                UserBehavior.created_at < current_start
            )
        ).group_by(
            UserBehavior.character_id
        ).subquery()

        # 计算增长率
        result = self.db.query(
            Character,
            func.coalesce(current.c.current_count, 0).label('current'),
            func.coalesce(previous.c.previous_count, 0).label('previous')
        ).outerjoin(
            current, Character.id == current.c.character_id
        ).outerjoin(
            previous, Character.id == previous.c.character_id
        ).filter(
            Character.is_active == True
        ).all()

        growth_data = []
        for char, curr, prev in result:
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
                'growth_rate': (growth_rate,2)
            })

        # 按增长率排序
        growth_data.sort(key=lambda x: x['growth_rate'], reverse=True)
        return growth_data[:limit]






