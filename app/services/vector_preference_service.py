# app/services/vector_preference_service.py
from typing import List

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.vector_recommend_repo import VectorRecommendRepository
from app.schemas.character import CharacterListItem

logger = get_logger(__name__)


class VectorPreferenceService:
    """基于向量相似度的偏好推荐服务"""

    # 行为权重配置
    BEHAVIOR_WEIGHTS = {
        'LIKE': 3.0,
        'CHAT': 2.0,
        'VIEW': 0.5
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = VectorRecommendRepository(db)
        self._feature_dim = 0
        self.tag_to_idx = {}
        self.cat_to_idx = {}

    async def _init_feature_maps(self):
        """初始化特征映射（延迟加载）"""
        if self._feature_dim > 0:
            return

        tags = await self.repo.get_all_tags()
        self.tag_to_idx = {tag.id: i for i, tag in enumerate(tags)}
        self.tag_count = len(tags)

        categories = await self.repo.get_all_categories()
        self.cat_to_idx = {cat.id: i + self.tag_count for i, cat in enumerate(categories)}

        self._feature_dim = self.tag_count + len(categories)
        logger.info(f"特征向量维度: {self._feature_dim}")

    async def _build_user_vector(self, user_id: int, days: int = 30) -> np.ndarray:
        """构建用户偏好向量"""
        await self._init_feature_maps()

        behaviors = await self.repo.get_user_behaviors(user_id, days)

        if not behaviors:
            return np.zeros(self._feature_dim)

        user_vector = np.zeros(self._feature_dim)

        for behavior in behaviors:
            char = behavior.character
            weight = self.BEHAVIOR_WEIGHTS.get(behavior.behavior_type, 1.0)

            for tag in char.tags:
                if tag.id in self.tag_to_idx:
                    user_vector[self.tag_to_idx[tag.id]] += weight

            for cat in char.categories:
                if cat.id in self.cat_to_idx:
                    user_vector[self.cat_to_idx[cat.id]] += weight

        norm = np.linalg.norm(user_vector)
        if norm > 0:
            user_vector = user_vector / norm

        return user_vector

    async def _build_character_vector(self, character) -> np.ndarray:
        """构建角色向量"""
        char_vector = np.zeros(self._feature_dim)

        for tag in character.tags:
            if tag.id in self.tag_to_idx:
                char_vector[self.tag_to_idx[tag.id]] = 1.0

        for cat in character.categories:
            if cat.id in self.cat_to_idx:
                char_vector[self.cat_to_idx[cat.id]] = 1.0

        return char_vector

    async def get_vector_recommendations(
        self,
        user_id: int,
        limit: int = 20,
        days: int = 30,
        threshold: float = 0.1
    ) -> List[CharacterListItem]:
        """基于向量相似度的推荐"""
        user_vector = await self._build_user_vector(user_id, days)

        if np.sum(user_vector) == 0:
            logger.info(f"用户 {user_id} 没有行为数据")
            return []

        all_chars = await self.repo.get_all_active_characters()
        excluded_ids = await self.repo.get_user_interacted_ids(user_id)

        results = []
        for char in all_chars:
            if char.id in excluded_ids:
                continue

            char_vector = await self._build_character_vector(char)
            similarity = cosine_similarity(
                user_vector.reshape(1, -1),
                char_vector.reshape(1, -1)
            )[0][0]

            if similarity >= threshold:
                results.append((char, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        top_chars = [char for char, _ in results[:limit]]

        return [CharacterListItem.model_validate(c) for c in top_chars]