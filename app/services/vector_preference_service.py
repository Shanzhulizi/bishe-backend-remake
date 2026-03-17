# app/services/vector_preference_service.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Optional
import logging

from app.repositories.vector_recommend_repo import VectorRecommendRepository
from app.schemas.character import CharacterListItem

logger = logging.getLogger(__name__)


class VectorPreferenceService:
    """基于向量相似度的偏好推荐服务"""

    # 行为权重配置
    BEHAVIOR_WEIGHTS = {
        'like': 3.0,
        'chat': 2.0,
        'view': 0.5
    }

    def __init__(self, db: Session):
        self.db = db
        self.repo = VectorRecommendRepository(db)
        self._init_feature_maps()

    def _init_feature_maps(self):
        """初始化特征映射（从数据库加载）"""
        # 获取所有标签
        tags = self.repo.get_all_tags()
        self.tag_to_idx = {tag.id: i for i, tag in enumerate(tags)}
        self.tag_count = len(tags)

        # 获取所有类别
        categories = self.repo.get_all_categories()
        self.cat_to_idx = {cat.id: i + self.tag_count for i, cat in enumerate(categories)}

        # 总特征维度
        self.feature_dim = self.tag_count + len(categories)

        # 反向映射（用于调试）
        self.idx_to_tag = {i: tag for tag, i in self.tag_to_idx.items()}
        self.idx_to_cat = {i: cat for cat, i in self.cat_to_idx.items()}

        logger.info(f"特征向量维度: {self.feature_dim} (标签: {self.tag_count}, 类别: {len(categories)})")

    def _build_user_vector(self, user_id: int, days: int = 30) -> np.ndarray:
        """
        构建用户偏好向量
        """
        # 获取用户行为
        behaviors = self.repo.get_user_behaviors(user_id, days)

        if not behaviors:
            logger.info(f"用户 {user_id} 没有行为数据")
            return np.zeros(self.feature_dim)

        # 初始化向量
        user_vector = np.zeros(self.feature_dim)

        # 累加权重
        for behavior in behaviors:
            char = behavior.character
            weight = self.BEHAVIOR_WEIGHTS.get(behavior.behavior_type, 1.0)

            # 标签权重
            for tag in char.tags:
                if tag.id in self.tag_to_idx:
                    user_vector[self.tag_to_idx[tag.id]] += weight

            # 类别权重
            for cat in char.categories:
                if cat.id in self.cat_to_idx:
                    user_vector[self.cat_to_idx[cat.id]] += weight

        # 归一化
        norm = np.linalg.norm(user_vector)
        if norm > 0:
            user_vector = user_vector / norm

        return user_vector

    def _build_character_vector(self, character) -> np.ndarray:
        """
        构建角色向量
        """
        char_vector = np.zeros(self.feature_dim)

        # 标签
        for tag in character.tags:
            if tag.id in self.tag_to_idx:
                char_vector[self.tag_to_idx[tag.id]] = 1.0

        # 类别
        for cat in character.categories:
            if cat.id in self.cat_to_idx:
                char_vector[self.cat_to_idx[cat.id]] = 1.0

        return char_vector

    def _calculate_similarities(
            self,
            user_vector: np.ndarray,
            characters: List,
            exclude_ids: List[int],
            threshold: float = 0.1
    ) -> List[Tuple]:
        """
        计算用户向量和所有角色向量的相似度
        """
        results = []

        for char in characters:
            if char.id in exclude_ids:
                continue

            char_vector = self._build_character_vector(char)
            similarity = cosine_similarity(
                user_vector.reshape(1, -1),
                char_vector.reshape(1, -1)
            )[0][0]

            if similarity >= threshold:
                results.append((char, similarity))

        return results

    def get_vector_recommendations(
            self,
            user_id: int,
            limit: int = 20,
            days: int = 30,
            threshold: float = 0.1
    ) -> List[CharacterListItem]:
        """
        基于向量相似度的推荐
        """
        # 1. 构建用户向量
        user_vector = self._build_user_vector(user_id, days)

        # 如果没有行为数据，返回空列表
        if np.sum(user_vector) == 0:
            logger.info(f"用户 {user_id} 没有行为数据")
            return []

        # 2. 获取所有角色
        all_chars = self.repo.get_all_active_characters()

        # 3. 获取已互动的角色ID
        excluded_ids = self.repo.get_user_interacted_ids(user_id)

        # 4. 计算相似度
        similarities = self._calculate_similarities(
            user_vector=user_vector,
            characters=all_chars,
            exclude_ids=excluded_ids,
            threshold=threshold
        )

        # 5. 排序并取前limit个
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_chars = [char for char, _ in similarities[:limit]]

        # 6. 转换为Schema
        return [CharacterListItem.model_validate(c) for c in top_chars]

    def get_recommendations_with_scores(
            self,
            user_id: int,
            limit: int = 20,
            days: int = 30
    ) -> List[Dict]:
        """
        获取带相似度分数的推荐（用于调试）
        """
        user_vector = self._build_user_vector(user_id, days)

        if np.sum(user_vector) == 0:
            return []

        all_chars = self.repo.get_all_active_characters()
        excluded_ids = self.repo.get_user_interacted_ids(user_id)

        similarities = self._calculate_similarities(
            user_vector=user_vector,
            characters=all_chars,
            exclude_ids=excluded_ids,
            threshold=0.0  # 不设阈值，全返回
        )

        similarities.sort(key=lambda x: x[1], reverse=True)

        result = []
        for char, score in similarities[:limit]:
            result.append({
                'character': CharacterListItem.model_validate(char),
                'similarity': round(float(score), 4),
                'match_tags': [t.name for t in char.tags if t.id in self.tag_to_idx],
                'match_cats': [c.name for c in char.categories if c.id in self.cat_to_idx]
            })

        return result

    def explain_recommendation(self, user_id: int, character_id: int) -> Dict:
        """
        解释推荐理由
        """
        # 获取用户向量
        user_vector = self._build_user_vector(user_id)

        # 获取角色
        from app.models.character import Character
        character = self.db.query(Character).get(character_id)
        if not character:
            return {"error": "角色不存在"}

        char_vector = self._build_character_vector(character)

        # 计算相似度
        similarity = cosine_similarity(
            user_vector.reshape(1, -1),
            char_vector.reshape(1, -1)
        )[0][0]

        # 找出匹配的特征
        matches = []

        # 匹配的标签
        for tag in character.tags:
            if tag.id in self.tag_to_idx:
                idx = self.tag_to_idx[tag.id]
                if user_vector[idx] > 0:
                    matches.append({
                        'type': 'tag',
                        'name': tag.name,
                        'user_weight': float(user_vector[idx]),
                        'contribution': float(user_vector[idx] * 1.0)  # 简化计算
                    })

        # 匹配的类别
        for cat in character.categories:
            if cat.id in self.cat_to_idx:
                idx = self.cat_to_idx[cat.id]
                if user_vector[idx] > 0:
                    matches.append({
                        'type': 'category',
                        'name': cat.name,
                        'user_weight': float(user_vector[idx]),
                        'contribution': float(user_vector[idx] * 1.0)
                    })

        # 按贡献度排序
        matches.sort(key=lambda x: x['contribution'], reverse=True)

        return {
            'user_id': user_id,
            'character_id': character_id,
            'character_name': character.name,
            'similarity': float(similarity),
            'top_matches': matches[:5],  # 只显示前5个
            'vector_dim': self.feature_dim,
            'user_vector_norm': float(np.linalg.norm(user_vector))
        }