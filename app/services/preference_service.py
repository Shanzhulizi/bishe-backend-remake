# app/services/preference_service.py
import logging
from collections import Counter
from typing import List

from sqlalchemy.orm import Session

from app.repositories.preference_repo import PreferenceRepository
from app.repositories.recommend_repo import RecommendRepository
from app.schemas.character import CharacterListItem

logger = logging.getLogger(__name__)


class PreferenceService:
    """用户偏好推荐服务"""

    # 行为权重
    BEHAVIOR_WEIGHTS = {
        'like': 3.0,
        'chat': 2.0,
        'view': 0.5
    }

    def __init__(self, db: Session):
        self.db = db
        self.repo = PreferenceRepository(db)
        self.hot_repo = RecommendRepository(db)

    def _analyze_user_preferences(self, behaviors: List) -> tuple:
        """
        分析用户偏好，返回喜欢的类别ID和标签ID
        """
        category_counter = Counter()
        tag_counter = Counter()

        for behavior in behaviors:
            char = behavior.character
            weight = self.BEHAVIOR_WEIGHTS.get(behavior.behavior_type, 1.0)

            for cat in char.categories:
                category_counter[cat.id] += weight
            for tag in char.tags:
                tag_counter[tag.id] += weight

        return (
            [cat_id for cat_id, _ in category_counter.most_common(5)],
            [tag_id for tag_id, _ in tag_counter.most_common(10)]
        )

    def get_personalized_recommendations(
            self,
            user_id: int,
            limit: int = 20,
            days: int = 30
    ) -> List[CharacterListItem]:
        """
        获取个性化推荐（只返回角色）
        """
        # 1. 获取用户行为
        behaviors = self.repo.get_user_recent_behaviors(user_id, days=days)

        if not behaviors:
            logger.info(f"用户 {user_id} 没有行为数据，返回热门推荐")
            # 没有行为数据，返回热门角色
            hot_chars = self.hot_repo.get_popular_characters(limit=limit, hours=7 * 24)
            return [CharacterListItem.model_validate(c) for c in hot_chars]

        # 2. 分析偏好
        top_categories, top_tags = self._analyze_user_preferences(behaviors)

        # 3. 获取已互动过的角色ID（用于排除）
        excluded_ids = self.repo.get_user_interacted_characters(user_id)

        # 4. 获取推荐
        candidates = self.repo.get_recommendations_by_preferences(
            category_ids=top_categories,
            tag_ids=top_tags,
            exclude_ids=excluded_ids,
            limit=limit
        )

        # 5. 转换为 Schema
        return [CharacterListItem.model_validate(c) for c in candidates]
