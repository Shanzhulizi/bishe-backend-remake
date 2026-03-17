# app/repositories/vector_recommend_repository.py
from typing import List

from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.models.character import Character
from app.models.tag import Tag
from app.models.user_behavior import UserBehavior


class VectorRecommendRepository:
    """向量推荐数据仓库"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_tags(self) -> List[Tag]:
        """获取所有标签"""
        return self.db.query(Tag).order_by(Tag.id).all()

    def get_all_categories(self) -> List[Category]:
        """获取所有类别"""
        return self.db.query(Category).order_by(Category.id).all()

    def get_user_behaviors(self, user_id: int, days: int) -> List[UserBehavior]:
        """获取用户行为"""
        from datetime import datetime, timedelta
        since = datetime.now() - timedelta(days=days)

        return self.db.query(UserBehavior).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since
        ).options(
            joinedload(UserBehavior.character)
                .joinedload(Character.categories),
            joinedload(UserBehavior.character)
                .joinedload(Character.tags)
        ).all()

    def get_all_active_characters(self) -> List[Character]:
        """获取所有活跃角色"""
        return self.db.query(Character).filter(
            Character.is_active == True
        ).options(
            joinedload(Character.categories),
            joinedload(Character.tags)
        ).all()

    def get_user_interacted_ids(self, user_id: int) -> List[int]:
        """获取用户互动过的角色ID"""
        results = self.db.query(
            UserBehavior.character_id
        ).filter(
            UserBehavior.user_id == user_id
        ).distinct().all()

        return [r[0] for r in results]