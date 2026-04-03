# app/api/v1/character_like_service.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db
from app.api.v1.auth import get_current_user
from app.core.constants import ResponseCode
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.character_like import CharacterLikeCount, CharacterLike, BatchLikeStatusRequest, \
    BatchLikeStatusResponse, LikeStatusResponse
from app.schemas.common import ResponseModel
from app.services.behavior_service import BehaviorService
from app.services.character_service import CharacterService

router = APIRouter()

logger = get_logger(__name__)


@router.get("/{character_id}/likes")
async def get_like_count(
        character_id: int,
        db: AsyncSession = Depends(get_async_db)
) -> ResponseModel[CharacterLikeCount]:
    """
    获取角色点赞数
    """
    try:
        character_service = CharacterService(db)
        like_count =await character_service.get_character_like_count(character_id)
    except Exception:
        return ResponseModel.error(code=ResponseCode.INTERNAL_ERROR, msg="获取角色信息失败")
    data = CharacterLikeCount(character_id=character_id, like_count=like_count)
    return ResponseModel.success(data=data)


@router.post("/{character_id}/like")
async def like_character(
        character_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
) -> ResponseModel[CharacterLike]:
    """
    点赞角色
    """
    logger.info(f"用户 {current_user.id} 点赞角色 {character_id}")
    try:

        character_service = CharacterService(db)

        behavior_service = BehaviorService(db)

        result =await behavior_service.get_like_record(current_user.id, character_id)
        if result:
            raise HTTPException(status_code=400, detail="你已经点过赞了")
        try:
            await behavior_service.record_like(user_id=current_user.id, character_id=character_id)
            await character_service.increment_like_count(character_id=character_id)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"记录点赞行为或增加点赞数失败: {e}")
            raise e

        # 获取最新的点赞数
        like_count =await  character_service.get_character_like_count(character_id)

        return ResponseModel.success(data=CharacterLike(
            character_id=character_id,
            like_count=like_count,
            is_liked=True))
    except Exception as e:
        logger.error(f"点赞失败: {e}")
        return ResponseModel.error(code=ResponseCode.LIKE_FAILED, msg=str(e))


@router.delete("/{character_id}/like")
async def unlike_character(
        character_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
) -> ResponseModel[CharacterLike]:
    """
    取消点赞
    """
    logger.info(f"用户 {current_user.id} 取消点赞角色 {character_id}")
    try:



        behavior_service = BehaviorService(db)

        character_service = CharacterService(db)
        result =await  behavior_service.get_like_record(current_user.id, character_id)

        if not result:
            return ResponseModel.error(code=ResponseCode.UNLIKE_FAILED, msg="你还没有点赞")
        try:
            await behavior_service.delete_records(user_id=current_user.id, character_id=character_id, behavior_type='like')

            await character_service.decrement_like_count(character_id=character_id)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"删除点赞行为或减少点赞数失败: {e}")
            raise e

        # 获取最新的点赞数
        like_count =await  character_service.get_character_like_count(character_id)
        return ResponseModel.success(data=CharacterLike(
            character_id=character_id,
            like_count=like_count,
            is_liked=False))

    except Exception as e:
        logger.error(f"取消点赞失败: {e}")
        return ResponseModel.error(code=ResponseCode.UNLIKE_FAILED, msg="取消点赞失败: " + str(e))


@router.get("/{character_id}/like/status")
async def get_like_status(
        character_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
) -> ResponseModel[LikeStatusResponse]:
    """
    获取点赞状态
    """
    character_service = CharacterService(db)
    is_liked = await character_service.get_character_like_status(current_user.id, character_id)

    return ResponseModel.success(data=LikeStatusResponse(
        character_id=character_id,
        is_liked=is_liked
    ))


@router.post("/likes/batch-status", response_model=ResponseModel[BatchLikeStatusResponse])
async def batch_get_like_status(
        request: BatchLikeStatusRequest,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """
    批量获取点赞状态（用于列表页）
    """
    try:
        character_service = CharacterService(db)
        character_ids = request.character_ids
        if not character_ids:
            return ResponseModel.success(data=BatchLikeStatusResponse(liked_map={}))

        liked_map =await  character_service.batch_get_like_status(current_user, character_ids)

        return ResponseModel.success(
            data=BatchLikeStatusResponse(liked_map=liked_map)
        )
    except Exception as e:
        logger.error(f"批量获取点赞状态失败: {e}")
        return ResponseModel.error(
            code=ResponseCode.INTERNAL_ERROR,
            msg=f"批量获取点赞状态失败: {str(e)}"
        )
