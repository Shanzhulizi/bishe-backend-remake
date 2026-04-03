from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_async_db
from app.core.logging import get_logger
from app.schemas.message import MessagePageResponse
from app.schemas.page import PageParams, Pagination
from app.services.behavior_service import BehaviorService
from app.services.character_service import CharacterService
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService

router = APIRouter()

logger = get_logger(__name__)


@router.get("/history/{character_id}")
async def get_history(character_id: int,
                      page: int = Query(1, ge=1),
                      page_size: int = Query(20, ge=1, le=100),
                      db=Depends(get_async_db), user=Depends(get_current_user)):
    try:
        conv_service = ConversationService(db)
        message_service = MessageService(db)
        conv = await conv_service.get_conv(user_id=user.id, character_id=character_id)
        if not conv:
            logger.info(f"用户 {user.id} 与角色 {character_id} 没有会话，正在创建新的会话")
            # 创建会话
            conv = await conv_service.create_conv(user_id=user.id, character_id=character_id)
        logger.info(f"会话：{conv.id}")
        total = await message_service.get_history_messages_count(conv.id)
        logger.info(f"历史消息总数 {total}")
        history = await message_service.get_history_messages(conv.id, PageParams(page=page, page_size=page_size))
        logger.info(f"获取历史消息数量 {len(history)}")

        behavior_service = BehaviorService(db)
        character_service = CharacterService(db)

        try:
            rt = await behavior_service.record_view(user_id=user.id, character_id=character_id)
            if rt:
                await character_service.increment_view_count(character_id)
            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"记录浏览行为或增加浏览量失败,{e}")
            raise e

        #  创建分页信息
        pagination = Pagination.create(
            page=page,
            page_size=page_size,
            total=total
        )

        # 5. 返回分页响应
        return MessagePageResponse(
            data=history,  # SQLAlchemy对象会自动转换为Message schema
            pagination=pagination
        )

    except Exception as e:
        logger.error(f"创建 ConversationService 失败: {e}")
        return MessagePageResponse(
            code=400,
            message="获取历史消息失败",
            data=[],
            pagination=Pagination.create(
                page=page,
                page_size=page_size,
                total=0
            )
        )
