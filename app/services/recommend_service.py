# app/services/hot_recommend_service.py

from datetime import datetime, timedelta

from app.core.logging import get_logger
from app.repositories.recommend_repo import RecommendRepository
from sqlalchemy.orm import Session

from app.schemas.character import CharacterListItem

logger = get_logger(__name__)


class RecommendService:

    def __init__(self, db: Session):
        self.recommend_repo = RecommendRepository(db)

    def get_hot(self, limit):
        """
            获取热门角色
        """
        characters= self.recommend_repo.get_hot_character(limit)
        logger.info(f"Fetched popular characters: {[char.name for char in characters]} with limit {limit}")


        popular_character = []
        for char in characters:
            # 方法A：直接使用 from_orm（如果配置了 orm_mode）
            popular_character.append(CharacterListItem.from_orm(char))

        return popular_character





    def get_popular(self, limit, hours):
        """
            获取流行榜（近期热度增长最多的角色）
        """

        characters = self.recommend_repo.get_popular_characters(limit, hours)

        return [CharacterListItem.model_validate(c) for c in characters]






    def get_trending(self, limit, hours):
        """
            获取流行榜（近期热度增长最快的角色）
        """

        chars = self.recommend_repo.get_trending(

            limit=limit, hours=hours, min_interaction = 100

        )
        logger.info("Trends data: id,name,avatar,recent,previous")
        logger.info(f"Trends data: {chars}")


        return chars
