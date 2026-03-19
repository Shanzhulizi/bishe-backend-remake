from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger
from app.schemas.message import MessagePageResponse
from app.schemas.page import PageParams, Pagination
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService

router = APIRouter()

logger = get_logger(__name__)

# TODO 需要在这里添加增加角色usage_count和修改last_use_at。因为每次加载历史对话就是在点击角色卡片
# TODO 需要添加分页功能，避免一次性加载过多消息导致性能问题
# TODO 这个我感觉要分层，但是目前先这样吧
"""
    这个我感觉要分层，但是目前先这样吧
"""


@router.get("/history/{character_id}")
async def get_history(character_id: int,
                      page: int = Query(1, ge=1),
                      page_size: int = Query(20, ge=1, le=100),
                      db=Depends(get_db), user=Depends(get_current_user)):

    try:
        conv_service = ConversationService(db)
        message_service = MessageService(db)
        conv = await conv_service.get_conv(user.id, character_id)
        total = message_service.get_history_messages_count(conv.id)
        logger.info(f"历史消息总数 {total}")
        history = message_service.get_history_messages(conv.id, PageParams(page=page, page_size=page_size))
        logger.info(f"获取历史消息数量 {len(history)}")
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
            message= "获取历史消息失败",
            data=[],
            pagination=Pagination.create(
                page=page,
                page_size=page_size,
                total=0
            )
        )