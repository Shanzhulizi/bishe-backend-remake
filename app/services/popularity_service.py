# app/services/popularity_service.py

from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.character import Character
from app.models.user_behavior import BehaviorType
from app.models.user_behavior import UserBehavior

logger = get_logger(__name__)


class PopularityService:
    """角色热度评分服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_score(
            self,
            character_id: int,
            weights: Dict[str, float] = None
    ) -> float:
        """
        计算单个角色的热度评分

        Args:
            character_id: 角色ID
            weights: 各指标的权重配置
        """
        if weights is None:
            weights = {
                'CHAT': 1.0,  # 聊天权重
                'LIKE': 2.0,  # 点赞权重
                'VIEW': 0.3,  # 浏览权重
                'RECENT': 1.5,  # 近期行为权重
                'DECAY': 0.1  # 时间衰减因子
            }

        # 获取角色
        stmt = select(Character).where(Character.id == character_id)
        result = await self.db.execute(stmt)
        character = result.scalar_one_or_none()

        if not character:
            return 0.0

        now = datetime.now()

        # 1. 总互动量分数
        total_score = (
                character.chat_count * weights['CHAT'] +
                character.like_count * weights['LIKE'] +
                character.view_count * weights['VIEW']
        )

        # 2. 近期热度分数（最近7天）
        week_ago = now - timedelta(days=7)
        recent_stats = await self.db.execute(
            select(
                func.sum(
                    func.case(
                        (UserBehavior.behavior_type == BehaviorType.CHAT, weights['CHAT']),
                        (UserBehavior.behavior_type == BehaviorType.LIKE, weights['LIKE']),
                        (UserBehavior.behavior_type == BehaviorType.VIEW, weights['VIEW']),
                        else_=0
                    )
                ).label('recent_score')
            ).where(
                UserBehavior.character_id == character_id,
                UserBehavior.created_at >= week_ago
            )
        )
        recent_score = recent_stats.scalar() or 0

        # 3. 时间衰减因子（越近的行为权重越高）
        if character.last_used_at:
            days_since_last = (now - character.last_used_at).days
            time_decay = max(0.0, 1 - (days_since_last * weights['DECAY']))
        else:
            time_decay = 0.0

        # 综合评分
        final_score = (
                total_score * 0.3 +
                recent_score * weights['RECENT'] * 0.5 +
                time_decay * 100 * 0.2
        )

        return round(final_score, 2)
