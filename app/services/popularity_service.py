# app/services/popularity_service.py
from sqlalchemy import func, desc, and_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from app.models.character import Character
from app.models.user_behavior import UserBehavior, BehaviorType

logger = logging.getLogger(__name__)


class PopularityService:
    """角色热度评分服务"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_score(
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
                'chat': 1.0,  # 聊天权重
                'like': 2.0,  # 点赞权重
                'view': 0.3,  # 浏览权重
                'recent': 1.5,  # 近期行为权重
                'decay': 0.1  # 时间衰减因子
            }

        # 获取角色
        character = self.db.query(Character).get(character_id)
        if not character:
            return 0.0

        now = datetime.now()

        # 1. 总互动量分数
        total_score = (
                character.chat_count * weights['chat'] +
                character.like_count * weights['like'] +
                character.view_count * weights['view']
        )

        # 2. 近期热度分数（最近7天）
        week_ago = now - timedelta(days=7)
        recent_stats = self.db.query(
            func.sum(
                func.case(
                    (UserBehavior.behavior_type == BehaviorType.CHAT, weights['chat']),
                    (UserBehavior.behavior_type == BehaviorType.LIKE, weights['like']),
                    (UserBehavior.behavior_type == BehaviorType.VIEW, weights['view']),
                    else_=0
                )
            ).label('recent_score')
        ).filter(
            UserBehavior.character_id == character_id,
            UserBehavior.created_at >= week_ago
        ).scalar() or 0

        # 3. 时间衰减因子（越近的行为权重越高）
        if character.last_used_at:
            days_since_last = (now - character.last_used_at).days
            time_decay = max(0, 1 - (days_since_last * weights['decay']))
        else:
            time_decay = 0

        # 综合评分
        final_score = (
                total_score * 0.3 +  # 总量占比30%
                recent_stats * weights['recent'] * 0.5 +  # 近期热度占比50%
                time_decay * 100 * 0.2  # 活跃度占比20%
        )

        return round(final_score, 2)
