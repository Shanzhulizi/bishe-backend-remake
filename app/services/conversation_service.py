import asyncio
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.local_model import local_model_summary
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.message import MessageBase
from app.services.message_service import MessageService

logger = get_logger(__name__)


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.message_service = MessageService(db)

    async def get_conv(self, user_id, character_id):
        conv = await self.conv_repo.get_active(user_id=user_id, character_id=character_id)
        return conv

    async def create_conv(self, user_id, character_id):
        conv = await self.conv_repo.create(user_id=user_id, character_id=character_id)
        return conv

    async def get_history_summary(self, conversation_id, user_id, character_id) -> str:
        """获取历史摘要（只读，不生成新摘要）"""
        # 只获取现有摘要，不触发新摘要生成
        existing_summary = await self.conv_repo.get_summary(conversation_id)
        return existing_summary or "无"

    async def update_summary(self,
                             conversation_id: int,
                             new_messages: List[MessageBase],
                             existing_summary: Optional[str] = None
                             ):
        """
        更新摘要（异步执行，不阻塞主流程）
        使用独立连接在后台执行
        """
        # ✅ 创建独立的数据库会话，不与主流程共享连接
        async with AsyncSessionLocal() as db:
            try:
                conv_repo = ConversationRepository(db)

                # 获取当前已总结的消息数量
                current_summary_count = await conv_repo.get_summary_count(conversation_id)

                # 生成新摘要
                logger.info(f"开始生成摘要: {len(new_messages)}条消息")
                if not existing_summary or existing_summary == "无":
                    new_summary = await local_model_summary(new_messages)
                else:
                    new_summary = await local_model_summary(new_messages, existing_summary)

                if not new_summary:
                    logger.warning(f"摘要生成失败: conversation_id={conversation_id}")
                    return

                # 保存摘要
                new_summary_count = current_summary_count + len(new_messages)
                success = await conv_repo.save_summary(
                    conversation_id=conversation_id,
                    summary=new_summary,
                    summary_count=new_summary_count
                )

                if success:
                    logger.info(
                        f"摘要更新成功: conversation_id={conversation_id}, "
                        f"已总结={new_summary_count}条消息"
                    )
                else:
                    logger.warning(f"摘要保存失败: conversation_id={conversation_id}")

            except Exception as e:
                logger.error(f"摘要更新失败: conversation_id={conversation_id}, error={e}")
                await db.rollback()
