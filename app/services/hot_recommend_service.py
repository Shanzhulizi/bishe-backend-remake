# app/services/hot_recommend_service.py

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.character import Character
from app.models.character_usage import CharacterLike, CharacterUsageLog


class HotRecommendService:

    @staticmethod
    def refresh_hot_scores(db: Session):
        """
        刷新所有角色的热度得分（定时任务调用）
        """
        characters = db.query(Character).all()

        # 获取全局最大值用于归一化
        max_usage = db.query(func.max(Character.usage_count)).scalar() or 1
        max_likes = db.query(func.max(Character.like_count)).scalar() or 1
        max_chats = db.query(func.max(Character.chat_count)).scalar() or 1

        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)

        for char in characters:
            # 计算近期使用量
            recent_usage = db.query(CharacterUsageLog).filter(
                CharacterUsageLog.character_id == char.id,
                CharacterUsageLog.created_at >= seven_days_ago
            ).count()

            # 计算近期点赞
            recent_likes = db.query(CharacterLike).filter(
                CharacterLike.character_id == char.id,
                CharacterLike.created_at >= seven_days_ago
            ).count()

            # 热度公式：总使用(30%) + 总点赞(20%) + 总对话(10%) + 近期使用(30%) + 近期点赞(10%)
            hot_score = (
                    (char.usage_count / max_usage) * 0.3 +
                    (char.like_count / max_likes) * 0.2 +
                    (char.chat_count / max_chats) * 0.1 +
                    min(recent_usage / 10, 1.0) * 0.3 +
                    min(recent_likes / 5, 1.0) * 0.1
            )

            char.popularity_score = round(hot_score, 3)

        db.commit()
