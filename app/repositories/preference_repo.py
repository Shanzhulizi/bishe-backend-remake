# app/repositories/preference_repo.py
from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Tuple
from collections import Counter

from app.models.user_behavior import UserBehavior, BehaviorType
from app.models.character import Character
from app.models.category import Category
from app.models.tag import Tag


class PreferenceRepository:
    """用户偏好数据仓库"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_recent_behaviors(self, user_id: int, days: int = 30, limit: int = 100) -> List[UserBehavior]:
        """
        获取用户最近的行为记录
        """
        from datetime import datetime, timedelta
        since = datetime.now() - timedelta(days=days)

        return self.db.query(UserBehavior).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since
        ).order_by(
            UserBehavior.created_at.desc()
        ).limit(limit).all()

    def get_user_interacted_characters(self, user_id: int, limit: int = 50) -> List[int]:
        """
        获取用户互动过的角色ID（去重）
        """
        results = self.db.query(
            UserBehavior.character_id
        ).filter(
            UserBehavior.user_id == user_id
        ).distinct().limit(limit).all()

        return [r[0] for r in results]

    def get_characters_by_ids(self, character_ids: List[int]) -> List[Character]:
        """
        根据ID列表获取角色
        """
        return self.db.query(Character).options(
            joinedload(Character.categories),
            joinedload(Character.tags)
        ).filter(
            Character.id.in_(character_ids),
            Character.is_active == True
        ).all()

    def get_recommendations_by_preferences(
            self,
            category_ids: List[int],
            tag_ids: List[int],
            exclude_ids: List[int],
            limit: int = 20
    ) -> List[Character]:
        """
        根据偏好推荐角色
        """
        query = self.db.query(Character).options(
            joinedload(Character.categories),
            joinedload(Character.tags)
        ).filter(
            Character.is_active == True,
            Character.id.notin_(exclude_ids)
        )

        # 优先匹配类别
        if category_ids:
            query = query.join(Character.categories).filter(
                Category.id.in_(category_ids)
            )

        # 再匹配标签
        if tag_ids:
            query = query.join(Character.tags).filter(
                Tag.id.in_(tag_ids)
            )

        return query.order_by(
            Character.popularity_score.desc()
        ).limit(limit).all()