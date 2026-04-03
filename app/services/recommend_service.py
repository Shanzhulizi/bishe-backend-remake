
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.character import Character
from app.repositories.recommend_repo import RecommendRepository
from app.schemas.character import CharacterListItem

logger = get_logger(__name__)


class RecommendService:

    def __init__(self, db: AsyncSession):
        self.recommend_repo = RecommendRepository(db)

    async def get_hot(self, limit):
        """
            获取热门角色
        """
        characters=await self.recommend_repo.get_hot_character(limit)
        logger.info(f"Fetched popular characters: {[char.name for char in characters]} with limit {limit}")
        return [CharacterListItem.model_validate(c) for c in characters]




    async def get_popular(self, limit, hours):
        """
            获取流行榜（近期热度增长最多的角色）
        """

        characters =await self.recommend_repo.get_popular_characters(limit, hours)
        logger.info( f"Fetched popular characters: {[char.name for char in characters]} with limit {limit} and hours {hours}")
        return [CharacterListItem.model_validate(c) for c in characters]






    async def get_trending(self, limit, hours):
        """
            获取流行榜（近期热度增长最快的角色）
        """
        # chars =await self.recommend_repo.get_trending(
        #     limit=limit, hours=hours, min_interaction = 100
        # )
        # # logger.info(f"Fetched trending characters: {[char.name for char in chars]} with limit {limit} and hours {hours}")
        # return chars

        trending_data = await self.recommend_repo.get_trending(limit, hours)
        return [CharacterListItem.model_validate(item['character']) for item in trending_data]


    async def get_hot_excluding(
            self,
            limit: int,
            exclude_ids: List[int] = None,
            days: int = 7
    ) -> List[Character]:
        """
        获取热门角色，排除指定的ID
        """
        if exclude_ids is None:
            exclude_ids = []

        # 从数据库获取热门角色，直接排除已推荐的
        hot_chars =await self.recommend_repo.get_popular_characters(
            limit=limit + len(exclude_ids),  # 多取一些，留出排除的空间
            hours=days * 24
        )

        # 过滤掉排除的ID
        filtered = [c for c in hot_chars if c.id not in exclude_ids]
        # logger.info(f"Fetched hot characters excluding IDs {exclude_ids}: {[char.name for char in filtered]} with limit {limit} and days {days}")
        return filtered[:limit]