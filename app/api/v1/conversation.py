
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository

router = APIRouter()



logger = get_logger(__name__)




# TODO
"""
    这个我感觉要分层，但是目前先这样吧
"""
@router.get("/history/{character_id}")
async def get_history(character_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    conversation = await ConversationRepository.get_active(db, user.id, character_id)
    if not conversation:
        return {"messages": []}

    msgs = await MessageRepository.get_messages_by_conversation(db, conversation.id)
    logger.info(f"获取历史消息数量 {len(msgs)}")
    # for m in msgs:
    #     logger.info(f"消息 {m.id} 来自 {m.sender_type} 内容 {m.content}")
    return {"messages": [{"id": m.id, "sender_type": m.sender_type, "content": m.content} for m in msgs]}
