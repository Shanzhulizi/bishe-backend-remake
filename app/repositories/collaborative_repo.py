# app/repositories/collaborative_repo.py
from datetime import datetime, timedelta
from typing import List, Tuple

from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload

from app.models.character import Character
from app.models.user_behavior import UserBehavior


class CollaborativeRepository:
    """协同过滤数据仓库"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_interacted_characters(self, user_id: int, days: int = 30) -> List[int]:
        """
        获取用户互动过的角色ID（带权重）
        """
        since = datetime.now() - timedelta(days=days)

        results = self.db.query(
            UserBehavior.character_id,
            func.count(UserBehavior.id).label('count')
        ).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.created_at >= since
        ).group_by(
            UserBehavior.character_id
        ).order_by(
            desc('count')
        ).limit(50).all()

        return [r[0] for r in results]

    def find_similar_users(
            self,
            user_id: int,
            user_characters: List[int],
            limit: int = 20
    ) -> List[Tuple[int, float]]:
        """
        找到相似用户（基于共同互动的角色）
        返回: [(user_id, 相似度分数)]
        """
        # 找也互动过这些角色的其他用户
        similar_users = self.db.query(
            UserBehavior.user_id,
            func.count(UserBehavior.character_id).label('common_count')
        ).filter(
            UserBehavior.character_id.in_(user_characters),
            UserBehavior.user_id != user_id
        ).group_by(
            UserBehavior.user_id
        ).order_by(
            desc('common_count')
        ).limit(limit).all()

        # 计算相似度分数
        total_chars = len(user_characters)
        result = []
        # Jaccard 相似度 = 交集大小 / 并集大小
        #               = 两个用户共同喜欢的角色数 / 两个用户喜欢的所有角色数
        for other_id, common_count in similar_users:
            similarity = common_count / total_chars  # Jaccard 相似度
            result.append((other_id, similarity))

        return result

    def get_users_preferred_characters(
            self,
            user_ids: List[int],
            exclude_ids: List[int],
            limit: int = 20
    ) -> List[Character]:
        """
        获取这些用户喜欢的角色
        """
        # 统计这些用户最常互动的角色
        popular_chars = self.db.query(
            UserBehavior.character_id,
            func.count(UserBehavior.id).label('popularity')
        ).filter(
            UserBehavior.user_id.in_(user_ids),
            ~UserBehavior.character_id.in_(exclude_ids)  # 排除当前用户已互动的
        ).group_by(
            UserBehavior.character_id
        ).order_by(
            desc('popularity')
        ).limit(limit).all()

        char_ids = [c[0] for c in popular_chars]

        # 获取完整角色信息
        return self.db.query(Character).options(
            joinedload(Character.categories),
            joinedload(Character.tags)
        ).filter(
            Character.id.in_(char_ids),
            Character.is_active == True
        ).all()