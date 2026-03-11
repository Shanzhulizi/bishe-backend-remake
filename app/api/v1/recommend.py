from typing import List, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.constants import ResponseCode
from app.core.logging import get_logger
from app.schemas.common import ResponseModel
from app.services.hot_recommend_service import HotRecommendService
from app.services.recommend_service import RecommendService

# app/api/v1/recommend.py

router = APIRouter()
logger = get_logger(__name__)


# 可选：一次性获取所有推荐的接口（方便首页加载）
@router.get("/all", response_model=ResponseModel[Dict])
async def get_all_recommendations(
        comprehensive_limit: int = 10,
        comprehensive_day: int = 7,
        trending_limit: int = 10,
        mixed_limit: int = 10,
        trending_hour: int = 7,
        db: Session = Depends(get_db)
):
    """
    一次性获取所有推荐（首页用）
    """
    try:
        logger.info("开始获取所有推荐")
        comprehensive = RecommendService.get_comprehensive_hot(
            db=db,
            limit=comprehensive_limit,
            days=comprehensive_day
        )
        logger.info(f"综合热门获取成功，数量: {len(comprehensive)}")
        trending = RecommendService.get_trending_hot(
            db=db,
            limit=trending_limit,
            hours=trending_hour
        )
        logger.info(f"近期飙升获取成功，数量: {len(trending)}")
        mixed = RecommendService.get_mixed_recommendations(
            db=db,
            limit=mixed_limit
        )
        logger.info(f"混合推荐获取成功，数量: {len(mixed)}")
        return ResponseModel.success(
            msg="获取所有推荐成功",
            data={
                "comprehensive": comprehensive,
                "trending": trending,
                "mixed": mixed
            }
        )
    except Exception as e:
        logger.error(f"获取所有推荐失败: {e}")
        return ResponseModel.error(
            code=ResponseCode.INTERNAL_ERROR,
            msg=f"获取所有推荐失败: {str(e)}"
        )


@router.get("/mixed", response_model=ResponseModel[List[Dict]])
async def get_mixed_recommendations(
        limit: int = 10,
        db: Session = Depends(get_db)
):
    """
    获取混合推荐
    综合热门 60% + 近期飙升 30% + 随机探索 10%
    """
    try:
        recommendations = RecommendService.get_mixed_recommendations(
            db=db,
            limit=limit
        )

        return ResponseModel.success(
            msg="获取混合推荐成功",
            data=recommendations
        )
    except Exception as e:
        logger.error(f"获取混合推荐失败: {e}")
        return ResponseModel.error(
            code=ResponseCode.INTERNAL_ERROR,
            msg=f"获取混合推荐失败: {str(e)}"
        )


@router.get("/hot")
async def get_hot_recommendations(
        limit: int = 20,
        days: int = 7,
        db: Session = Depends(get_db)
) -> ResponseModel:
    """
    获取热门角色推荐
    - limit: 返回数量
    - days: 计算近几天的热度
    """
    try:
        recommendations = RecommendService.get_comprehensive_hot(
            db=db,
            limit=limit,
            days=days
        )

        return ResponseModel.success(
            msg="获取热门推荐成功",
            data=recommendations
        )
    except Exception as e:
        logger.error(f"获取热门推荐失败: {e}")
        return ResponseModel.error(
            code=ResponseCode.INTERNAL_ERROR,
            msg=f"获取热门推荐失败: {str(e)}"
        )


@router.get("/trending")
async def get_trending_recommendations(
        limit: int = 10,
        hours: int = 24,
        db: Session = Depends(get_db)
) -> ResponseModel:
    """
    获取飙升榜（近期热度增长最快的角色）
    - limit: 返回数量
    - hours: 计算最近多少小时的增长
    """
    try:
        trending = RecommendService.get_trending_hot(
            db=db,
            limit=limit,
            hours=hours
        )

        return ResponseModel.success(
            msg="获取飙升榜成功",
            data=trending
        )
    except Exception as e:
        logger.error(f"获取飙升榜失败: {e}")
        return ResponseModel.error(
            code=ResponseCode.INTERNAL_ERROR,
            msg=f"获取飙升榜失败: {str(e)}"
        )


@router.post("/refresh-hot-scores")
async def refresh_hot_scores(
        db: Session = Depends(get_db)
) -> ResponseModel:
    """
    手动刷新热度得分（通常由定时任务自动执行）
    """
    try:
        HotRecommendService.refresh_hot_scores(db)
        return ResponseModel.success(msg="热度得分刷新成功")
    except Exception as e:
        logger.error(f"刷新热度得分失败: {e}")
        return ResponseModel.error(
            code=ResponseCode.INTERNAL_ERROR,
            msg=f"刷新热度得分失败: {str(e)}"
        )
