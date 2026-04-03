# app/services/collaborative_service.py
import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.collaborative_repo import CollaborativeRepository
from app.repositories.preference_repo import PreferenceRepository
from app.schemas.character import CharacterListItem

logger = logging.getLogger(__name__)


class CollaborativeService:
    """协同过滤推荐服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CollaborativeRepository(db)
        self.pref_repo = PreferenceRepository(db)


    async def get_collaborative_recommendations(
            self,
            user_id: int,
            limit: int = 20,
            days: int = 30
    ) -> List[CharacterListItem]:
        """
        基于协同过滤的推荐
        找相似用户喜欢的角色
        """
        # 1. 获取当前用户互动的角色
        user_chars =await self.repo.get_user_interacted_characters(user_id, days)

        if not user_chars:
            logger.info(f"用户 {user_id} 没有互动记录，返回空列表")
            return []

        # 2. 找相似用户
        similar_users =await self.repo.find_similar_users(
            user_id=user_id,
            user_characters=user_chars,
            limit=20  # 找20个相似用户
        )

        if not similar_users:
            logger.info(f"没找到相似用户")
            return []

        # 3. 获取这些用户喜欢的角色
        similar_user_ids = [u[0] for u in similar_users]
        recommended_chars =await self.repo.get_users_preferred_characters(
            user_ids=similar_user_ids,
            exclude_ids=user_chars,  # 排除已互动过的
            limit=limit
        )

        # 4. 转换为 Schema
        return [CharacterListItem.model_validate(c) for c in recommended_chars]

    # async def get_hybrid_recommendations(
    #         self,
    #         user_id: int,
    #         limit: int = 20
    # ) -> List[CharacterListItem]:
    #     """
    #     混合推荐：协同过滤 + 热门补充
    #     """
    #     # 协同过滤推荐
    #     collab_recs =await self.get_collaborative_recommendations(
    #         user_id=user_id,
    #         limit=limit
    #     )
    #
    #     # 如果不够，用热门补充
    #     if len(collab_recs) < limit:
    #         from .recommend_service import RecommendService
    #         hot_service = RecommendService(self.db)
    #         hot_recs =await hot_service.get_popular_characters(
    #             limit=limit - len(collab_recs)
    #         )
    #         collab_recs.extend(hot_recs)
    #
    #     return collab_recs