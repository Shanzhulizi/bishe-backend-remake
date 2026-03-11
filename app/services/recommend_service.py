# app/services/hot_recommend_service.py

from datetime import datetime, timedelta

from app.core.logging import get_logger
from app.repositories.recommend_repo import RecommendRepository

logger= get_logger(__name__)

class RecommendService:

    @classmethod
    def get_comprehensive_hot(cls, db, limit, days):
        """
            获取热门角色（综合热度算法）
        """
        popular_character = RecommendRepository.get_popular_character(db,limit)

        return popular_character

    @classmethod
    def get_trending_hot(cls, db, limit, hours):
        """
            获取飙升榜（近期热度增长最快的角色）
        """
        now = datetime.now()
        recent_start = now - timedelta(hours=hours)
        previous_start = recent_start - timedelta(hours=hours)

        # 计算增长率
        trends = RecommendRepository.get_trends(db, previous_start, recent_start)
        logger.info("Trends data: id,name,avatar,recent,previous")
        logger.info(f"Trends data: {trends}")

        result = []
        for trend in trends:
            # 计算增长率
            if trend.previous > 0:
                growth = (trend.recent - trend.previous) / trend.previous
            else:
                growth = trend.recent * 2  # 从0到有的，给个基础增长值

            result.append({
                'id': trend.id,
                'name': trend.name,
                'avatar': trend.avatar,
                'recent_usage': trend.recent,
                'previous_usage': trend.previous,
                'growth_rate': round(growth, 2)
            })

        # 按增长率排序
        result.sort(key=lambda x: x['growth_rate'], reverse=True)
        return result[:limit]

    # TODO 这个是真正要做好的，结合众多数据进行推算的推荐算法，包括tags，用户喜好，角色属性等
    # 目前直接用热度只是为了跑通功能
    @classmethod
    def get_mixed_recommendations(cls, db, limit):
        popular_character = RecommendRepository.get_popular_character(db, limit)

        return popular_character
