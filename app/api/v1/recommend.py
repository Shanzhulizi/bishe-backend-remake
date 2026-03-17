from typing import List, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.constants import ResponseCode
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.collaborative_service import CollaborativeService
from app.services.hot_recommend_service import HotRecommendService
from app.services.preference_service import PreferenceService

from app.services.recommend_service import RecommendService

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
import random

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.preference_service import PreferenceService
from app.services.collaborative_service import CollaborativeService
from app.services.recommend_service import RecommendService
from app.schemas.recommend import RecommendResponse
from app.schemas.character import CharacterListItem
from app.services.recommend_service import RecommendService
from app.schemas.character import CharacterListItem
from app.schemas.recommend import RecommendResponse
from app.services.vector_preference_service import VectorPreferenceService

router = APIRouter()
logger = get_logger(__name__)




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
        hours: int = 7 * 24,
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
async def get_personalized_recommendations(
        limit: int = Query(20, ge=1, le=50),
        days: int = Query(30, ge=7, le=90),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取个性化推荐（猜你喜欢）
    """
    try:
        service = PreferenceService(db)
        # TODO 以后再使用向量相似度优化偏好推荐算法，目前先使用简单的基于用户行为和SQL的推荐
        characters = service.get_personalized_recommendations(
            user_id=current_user.id,
            limit=limit,
            days=days
        )

        return RecommendResponse(
            code=200,
            msg="获取个性化推荐成功",
            data=characters,
            total=len(characters),
            scene="personalized"
        )

    except Exception as e:
        logger.error(f"获取个性化推荐失败: {e}")
        return RecommendResponse(
            code=500,
            msg="获取推荐失败",
            data=[],
            total=0,
            scene="personalized"
        )


@router.get("/pretend-vector", response_model=RecommendResponse)
async def get_vector_recommendations(
        limit: int = Query(20, ge=1, le=50),
        days: int = Query(30, ge=7, le=90),
        threshold: float = Query(0.1, ge=0.0, le=1.0),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    基于向量相似度的个性化推荐（更精准）
    - 将用户偏好和角色都转为向量
    - 计算余弦相似度
    - 返回相似度最高的角色
    """
    try:
        service = VectorPreferenceService(db)

        characters = service.get_vector_recommendations(
            user_id=current_user.id,
            limit=limit,
            days=days,
            similarity_threshold=threshold
        )

        return RecommendResponse(
            code=200,
            msg="获取向量推荐成功",
            data=characters,
            total=len(characters),
            scene="vector_personalized"
        )

    except Exception as e:
        logger.error(f"获取向量推荐失败: {e}")
        return RecommendResponse(
            code=500,
            msg="获取推荐失败",
            data=[],
            total=0,
            scene="vector_personalized"
        )


@router.get("/similar", response_model=RecommendResponse)
async def similar_recommend(
        limit: int = Query(20, ge=1, le=50),
        days: int = Query(30, ge=7, le=90),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    协同过滤推荐
    - 找和你有相似喜好的用户
    - 推荐他们喜欢的角色
    """
    try:
        service = CollaborativeService(db)

        characters = service.get_collaborative_recommendations(
            user_id=current_user.id,
            limit=limit,
            days=days
        )

        return RecommendResponse(
            code=200,
            msg="获取协同推荐成功",
            data=characters,
            total=len(characters),
            scene="collaborative"
        )

    except Exception as e:
        logger.error(f"获取协同推荐失败: {e}")
        return RecommendResponse(
            code=500,
            msg="获取推荐失败",
            data=[],
            total=0,
            scene="collaborative"
        )


@router.get("/mix", response_model=RecommendResponse)
async def mix_recommend(
        limit: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    混合推荐策略
    - 40% 基于用户偏好（猜你喜欢）
    - 30% 基于协同过滤（相似用户）
    - 30% 随机热门（探索新内容）
    """
    try:
        # 初始化服务
        pref_service = PreferenceService(db)
        collab_service = CollaborativeService(db)
        hot_service = RecommendService(db)

        # 计算各策略目标数量
        pref_target = int(limit * 0.4)  # 40%
        collab_target = int(limit * 0.3)  # 30%
        hot_target = limit - pref_target - collab_target  # 30%

        # 存储所有已推荐ID
        recommended_ids = set()

        # 1. 用户偏好推荐
        pref_characters = pref_service.get_personalized_recommendations(
            user_id=current_user.id,
            limit=pref_target*3+10,  # 多取一些候选，后面随机打乱再选
        )

        # 随机打乱候选列表
        random.shuffle(pref_characters)

        # 取前 pref_target 个
        pref_chars = pref_characters[:pref_target]
        for char in pref_chars:
            recommended_ids.add(char.id)

        # 2. 协同过滤推荐
        collaborative_chars = collab_service.get_collaborative_recommendations(
            user_id=current_user.id,
            limit=collab_target*3+10
        )
        # 过滤掉已经在偏好推荐中的
        collaborative_chars = [c for c in collaborative_chars if c.id not in recommended_ids]

        # 随机打乱候选列表
        random.shuffle(collaborative_chars)

        # 取前 collab_target 个
        collab_chars = collaborative_chars[:collab_target]

        for char in collab_chars:
            recommended_ids.add(char.id)

        # 3. 热门推荐（自动排除已推荐的）
        hot_chars = []
        if hot_target > 0:
            hot_candidates = hot_service.get_hot_excluding(
                limit=hot_target * 3+10,  # 多取3倍
                exclude_ids=list(recommended_ids),
                days=7
            )

            # 随机打乱候选列表
            random.shuffle(hot_candidates)

            # 取前 hot_target 个
            hot_chars = hot_candidates[:hot_target]

        for char in hot_chars:
            recommended_ids.add(char.id)

        # 合并结果
        result = pref_chars + collab_chars + hot_chars

        return RecommendResponse(
            code=200,
            msg="获取混合推荐成功",
            data=result,
            total=len(result),
            scene="mix"
        )

    except Exception as e:
        logger.error(f"获取混合推荐失败: {e}")
        return RecommendResponse(
            code=500,
            msg="获取推荐失败",
            data=[],
            total=0,
            scene="mix"
        )
