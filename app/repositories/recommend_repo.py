# app/services/hot_recommend_service.py
from operator import and_, or_

from sqlalchemy import func

from app.models.character import Character
from app.models.character_usage import CharacterUsageLog
from app.schemas.recommend import CharacterRecommendResponse


class RecommendRepository:

    @classmethod
    def get_popular_character(cls, db, limit):
        result = db.query(
            Character.id,
            Character.name,
            Character.avatar,
            Character.description,
            Character.popularity_score,
            Character.like_count,
            Character.usage_count,
            Character.chat_count
        ).order_by(
            Character.popularity_score.desc()
        ).limit(limit ).all()

        # 转换为 Pydantic 模型（自动处理序列化）
        popular_characters = [
            CharacterRecommendResponse(**row._asdict())
            for row in result
        ]

        return popular_characters

    @classmethod
    def get_recent_usage(cls, db, recent_start):
        recent_usage = db.query(
            CharacterUsageLog.character_id,
            func.count(CharacterUsageLog.id).label('count')
        ).filter(
            CharacterUsageLog.created_at >= recent_start
        ).group_by(
            CharacterUsageLog.character_id
        ).subquery()

        return recent_usage

    @classmethod
    def get_previous_usage(cls, db, previous_start, recent_start):
        previous_usage = db.query(
            CharacterUsageLog.character_id,
            func.count(CharacterUsageLog.id).label('count')
        ).filter(
            and_(
                CharacterUsageLog.created_at >= previous_start,
                CharacterUsageLog.created_at < recent_start
            )
        ).group_by(
            CharacterUsageLog.character_id
        ).subquery()
        return previous_usage

    @classmethod
    def get_trends(cls, db, previous_start, recent_start):
        # 近期使用量
        recent_usage = cls.get_recent_usage(db, recent_start)

        # 前期使用量
        previous_usage = cls.get_previous_usage(db, previous_start, recent_start)
        # 计算增长率
        trends = db.query(
            Character.id,
            Character.name,
            Character.avatar,
            func.coalesce(recent_usage.c.count, 0).label('recent'),
            func.coalesce(previous_usage.c.count, 0).label('previous')
        ).outerjoin(
            recent_usage,
            recent_usage.c.character_id == Character.id
        ).outerjoin(
            previous_usage,
            previous_usage.c.character_id == Character.id
        ).filter(
            or_(
                recent_usage.c.count > 0,
                previous_usage.c.count > 0
            )
        ).all()

        return trends
