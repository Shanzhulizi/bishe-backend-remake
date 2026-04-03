import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.local_model import local_model_summary
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.page import PageParams
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

    #
    # async def check_and_update_summary(self, conversation_id, user_id, character_id):
    #     """检查并更新摘要（异步执行，不阻塞主流程）"""
    #     try:
    #         # 获取统计信息
    #         summarized_count = await self.conv_repo.get_summary_count(conversation_id)
    #         chat_count = await self.conv_repo.get_chat_count(conversation_id)
    #         unsummarized_count = chat_count - summarized_count
    #
    #         # 判断是否需要更新
    #         need_update = False
    #         new_messages = []
    #
    #         if summarized_count == 0 and chat_count >= 40:
    #             need_update = True
    #             new_messages = await self.message_service.get_history_messages(
    #                 conversation_id, PageParams(page=1, page_size=20)
    #             )
    #             new_summarized_count = 20
    #
    #         elif unsummarized_count >= 20:
    #             need_update = True
    #             page = (summarized_count // 20) + 1
    #             new_messages = await self.message_service.get_history_messages(
    #                 conversation_id, PageParams(page=page, page_size=20)
    #             )
    #             new_summarized_count = summarized_count + len(new_messages)
    #
    #         if need_update and new_messages:
    #             # 生成摘要
    #             existing_summary = await self.conv_repo.get_summary(conversation_id)
    #             if summarized_count == 0:
    #                 new_summary = await local_model_summary(new_messages)
    #             else:
    #                 new_summary = await local_model_summary(new_messages, existing_summary)
    #
    #             # 保存摘要
    #             await self.conv_repo.save_summary(
    #                 conversation_id=conversation_id,
    #                 summary=new_summary,
    #                 summary_count=new_summarized_count
    #             )
    #             logger.info(f"摘要更新完成: {conversation_id}")
    #
    #     except Exception as e:
    #         logger.error(f"摘要更新失败: {e}")



    async def check_and_update_summary(self, conversation_id, user_id, character_id):
        """
        检查并更新摘要（异步执行，不阻塞主流程）
        使用独立连接在后台执行
        """
        try:
            # ✅ 创建独立的后台任务，使用新的数据库连接
            asyncio.create_task(
                self._do_update_summary(conversation_id, user_id, character_id)
            )
            logger.debug(f"摘要更新任务已启动: conversation_id={conversation_id}")
        except Exception as e:
            logger.error(f"启动摘要更新任务失败: {e}")

    async def _do_update_summary(self, conversation_id, user_id, character_id):
        """
        实际执行摘要更新 - 使用独立的数据库连接
        """
        # ✅ 创建独立的数据库会话，不与主流程共享连接
        async with AsyncSessionLocal() as db:
            try:
                # 使用独立连接的 repository
                conv_repo = ConversationRepository(db)
                message_service = MessageService(db)  # MessageService 内部会使用 db

                # 获取统计信息
                summarized_count = await conv_repo.get_summary_count(conversation_id)
                chat_count = await conv_repo.get_chat_count(conversation_id)
                unsummarized_count = chat_count - summarized_count

                logger.debug(
                    f"摘要统计: conversation_id={conversation_id}, "
                    f"总消息={chat_count}, 已总结={summarized_count}, "
                    f"未总结={unsummarized_count}"
                )

                # 判断是否需要更新
                need_update = False
                new_messages = []
                new_summarized_count = summarized_count

                if summarized_count == 0 and chat_count >= 40:
                    need_update = True
                    # ✅ 调用你的 get_messages_page，它会正确处理正序/倒序
                    new_messages = await message_service.get_history_messages(
                        conversation_id,
                        PageParams(page=1, page_size=20)
                    )
                    new_summarized_count = 20
                    logger.info(f"触发首次摘要更新: 前20条消息")

                elif unsummarized_count >= 20:
                    need_update = True
                    # ✅ 计算页码：已总结数量 ÷ 20 + 1
                    page = (summarized_count // 20) + 1
                    new_messages = await message_service.get_history_messages(
                        conversation_id,
                        PageParams(page=page, page_size=20)
                    )
                    new_summarized_count = summarized_count + len(new_messages)
                    logger.info(f"触发增量摘要更新: 第{page}页，共{len(new_messages)}条新消息")

                if need_update and new_messages:
                    # 获取现有摘要
                    existing_summary = await conv_repo.get_summary(conversation_id)

                    # 生成摘要（LLM 调用，不占用数据库连接）
                    logger.info(f"开始生成摘要: {len(new_messages)}条消息")
                    if summarized_count == 0:
                        new_summary = await local_model_summary(new_messages)
                    else:
                        new_summary = await local_model_summary(new_messages, existing_summary)

                    # 保存摘要
                    success = await conv_repo.save_summary(
                        conversation_id=conversation_id,
                        summary=new_summary,
                        summary_count=new_summarized_count
                    )

                    if success:
                        logger.info(f"摘要更新成功: conversation_id={conversation_id}, "
                                    f"已总结={new_summarized_count}条消息")
                    else:
                        logger.warning(f"摘要保存失败: conversation_id={conversation_id}")

            except Exception as e:
                logger.error(f"摘要更新失败: conversation_id={conversation_id}, error={e}")
                await db.rollback()