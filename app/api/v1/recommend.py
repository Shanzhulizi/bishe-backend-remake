from typing import List, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.constants import ResponseCode
from app.core.logging import get_logger
from app.schemas.common import ResponseModel
from app.services.hot_recommend_service import HotRecommendService

from app.services.recommend_service import RecommendService

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.services.recommend_service import RecommendService
from app.schemas.character import CharacterListItem
from app.schemas.recommend import RecommendResponse

router = APIRouter()
logger = get_logger(__name__)


#
# 可选：一次性获取所有推荐的接口（方便首页加载）
# @router.get("/all", response_model=ResponseModel[Dict])
# async def get_all_recommendations(
#         comprehensive_limit: int = 10,
#         comprehensive_day: int = 7,
#         trending_limit: int = 10,
#         mixed_limit: int = 10,
#         trending_hour: int = 7,
#         db: Session = Depends(get_db)
# ):
#     """
#     一次性获取所有推荐（首页用）
#     """
#     try:
#         recommend_service = RecommendService(db)
#         logger.info("开始获取所有推荐")
#         comprehensive = recommend_service.get_popular(
#
#             limit=comprehensive_limit,
#
#         )
#         logger.info(f"综合热门获取成功，数量: {len(comprehensive)}")
#         trending = recommend_service.get_trending_hot(
#
#             limit=trending_limit,
#             hours=trending_hour
#         )
#         logger.info(f"近期飙升获取成功，数量: {len(trending)}")
#         mixed = recommend_service.get_mixed_recommendations(
#
#             limit=mixed_limit
#         )
#         logger.info(f"混合推荐获取成功，数量: {len(mixed)}")
#         return ResponseModel.success(
#             msg="获取所有推荐成功",
#             data={
#                 "comprehensive": comprehensive,
#                 "trending": trending,
#                 "mixed": mixed
#             }
#         )
#     except Exception as e:
#         logger.error(f"获取所有推荐失败: {e}")
#         return ResponseModel.error(
#             code=ResponseCode.INTERNAL_ERROR,
#             msg=f"获取所有推荐失败: {str(e)}"
#         )
#
#
# @router.get("/mixed", response_model=ResponseModel[List[Dict]])
# async def get_mixed_recommendations(
#         limit: int = 10,
#         db: Session = Depends(get_db)
# ):
#     """
#     获取混合推荐
#     综合热门 60% + 近期飙升 30% + 随机探索 10%
#     """
#     try:
#         recommend_service = RecommendService(db)
#         recommendations = recommend_service.get_mixed_recommendations(
#
#             limit=limit
#         )
#
#         return ResponseModel.success(
#             msg="获取混合推荐成功",
#             data=recommendations
#         )
#     except Exception as e:
#         logger.error(f"获取混合推荐失败: {e}")
#         return ResponseModel.error(
#             code=ResponseCode.INTERNAL_ERROR,
#             msg=f"获取混合推荐失败: {str(e)}"
#         )
#
#
# @router.get("/hot")
# async def get_hot_recommendations(
#         limit: int = 20,
#         days: int = 7,
#         db: Session = Depends(get_db)
# ) -> ResponseModel:
#     """
#     获取热门角色推荐
#     - limit: 返回数量
#     - days: 计算近几天的热度
#     """
#     try:
#         recommend_service = RecommendService(db)
#         recommendations = recommend_service.get_comprehensive_hot(
#
#             limit=limit
#         )
#
#         return ResponseModel.success(
#             msg="获取热门推荐成功",
#             data=recommendations
#         )
#     except Exception as e:
#         logger.error(f"获取热门推荐失败: {e}")
#         return ResponseModel.error(
#             code=ResponseCode.INTERNAL_ERROR,
#             msg=f"获取热门推荐失败: {str(e)}"
#         )
#
#
# @router.get("/trending")
# async def get_trending_recommendations(
#         limit: int = 10,
#         hours: int = 24,
#         db: Session = Depends(get_db)
# ) -> ResponseModel:
#     """
#     获取飙升榜（近期热度增长最快的角色）
#     - limit: 返回数量
#     - hours: 计算最近多少小时的增长
#     """
#     try:
#         recommend_service = RecommendService(db)
#         trending = recommend_service.get_trending_hot(
#
#             limit=limit,
#             hours=hours
#         )
#
#         return ResponseModel.success(
#             msg="获取飙升榜成功",
#             data=trending
#         )
#     except Exception as e:
#         logger.error(f"获取飙升榜失败: {e}")
#         return ResponseModel.error(
#             code=ResponseCode.INTERNAL_ERROR,
#             msg=f"获取飙升榜失败: {str(e)}"
#         )


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


@router.get("/hot", response_model=RecommendResponse)
async def get_hot(
        limit: int = 20,
        db: Session = Depends(get_db)
):
    """
        热门推荐
    """
    try:
        recommend_service = RecommendService(db)
        recommendations = recommend_service.get_popular(

            limit=limit
        )

        return RecommendResponse(
            msg="获取热门推荐成功",
            data=recommendations,
            total=len(recommendations),
            scene="hot"
        )
    except Exception as e:
        logger.error(f"获取热门推荐失败: {e}")
        return RecommendResponse(
            code=400,
            msg="获取热门推荐失败",

        )


@router.get("/popular", response_model=RecommendResponse)
async def get_popular(
        limit: int = 20,
                      hours: int = 7*24,
                      db: Session = Depends(get_db)
                      ):
    """
        近期流行
    """

    try:
        recommend_service = RecommendService(db)
        recommendations = recommend_service.get_popular(

            limit=limit,
            hours=hours
        )

        return RecommendResponse(
            msg="获取热门推荐成功",
            data=recommendations,
            total=len(recommendations),
            scene="hot"
        )
    except Exception as e:
        logger.error(f"获取热门推荐失败: {e}")
        return RecommendResponse(
            code=400,
            msg="获取热门推荐失败",

        )



@router.get("/trending", response_model=RecommendResponse)
async def get_popular(
        limit: int = 20,
                      hours: int = 24,
                      db: Session = Depends(get_db)
                      ):
    """
        近期飙升
    """

    try:
        recommend_service = RecommendService(db)
        recommendations = recommend_service.get_trending(

            limit=limit,
            hours=hours
        )

        return RecommendResponse(
            msg="获取热门推荐成功",
            data=recommendations,
            total=len(recommendations),
            scene="hot"
        )
    except Exception as e:
        logger.error(f"获取热门推荐失败: {e}")
        return RecommendResponse(
            code=400,
            msg="获取热门推荐失败",

        )






@router.get("/pretend", response_model=RecommendResponse)
async def get_popular(
        db: Session = Depends(get_db)
):
    """
        获取用户偏好的相似角色
    """
    service = RecommendService(db)
    response = RecommendResponse
    response.data
    response.msg

    return response


@router.get("/similar", response_model=RecommendResponse)
async def get_popular(
        db: Session = Depends(get_db)
):
    """
        协同过滤
        找相似用户
        推荐这些用户喜欢的角色
    """
    service = RecommendService(db)
    response = RecommendResponse
    response.data
    response.msg

    return response


@router.get("/mix", response_model=RecommendResponse)
async def get_popular(
        db: Session = Depends(get_db)
):
    """
        混合策略= 用户偏好40 + 协同过滤30 + 随机热门30
    """
    service = RecommendService(db)
    response = RecommendResponse
    response.data
    response.msg

    return response


# @router.get("/ontime", response_model=RecommendResponse)
# async def get_popular(
#         db: Session = Depends(get_db)
# ):
#     """
#         实时推荐
#         这是在退出某个角色的聊天界面后，随机可能会弹出这个
#         看了这个角色的人还看了什么角色
#     """
#     service = RecommendService(db)
#     response = RecommendResponse
#     response.data
#     response.msg
#
#     return response
