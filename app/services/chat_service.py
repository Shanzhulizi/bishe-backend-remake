import asyncio
from asyncio import Semaphore
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.ai.client import chat_completion_stream
from app.ai.deepseek import deepseek_chat_stream
from app.ai.prompt_builder import build_system_prompt
from app.core.logging import get_logger
from app.repositories.character_repo import CharacterRepository
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.page import PageParams
from app.services.behavior_service import BehaviorService
from app.services.character_service import CharacterService
from app.services.conversation_service import ConversationService
from app.services.ethics_service import EthicsService, ethics_service
from fastapi import BackgroundTasks

logger = get_logger(__name__)


class ChatService:
    _llm_semaphore = Semaphore(2)

    def __init__(self, db: AsyncSession):
        self.db = db
        # self.executor = ThreadPoolExecutor(max_workers=4)

        self.character_repo = CharacterRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        # 3b模型会造成误判，如：我想把欺负我的人捅死，3b会返回is_safe=True
        # self.ethics_service = EthicsService("qwen2.5:3b")
        self.conversation_service = ConversationService(db)

    async def send_message_stream(
            self,
            user_id: int,
            character_id: int,
            content: str,
    ) -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()
        reply_buffer = ""
        conversation = None
        stream_success = False

        try:

            # 1. 检查角色
            character = await self.character_repo.get_by_id(character_id)
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")

            # 2. 获取或创建会话
            conversation = await self.conversation_repo.get_active(user_id, character_id)
            if not conversation:
                conversation = await self.conversation_repo.create(user_id, character_id)

            # ✅ 可以并行执行（它们之间没有依赖关系）
            recent_history, history_summary = await asyncio.gather(
                self.message_repo.get_messages_page(conversation.id, PageParams(page=1, page_size=20)),
                self.conversation_service.get_history_summary(conversation.id, user_id, character_id)
            )

            #  这里应该搞吗？这里搞了那提示词不就没用了吗？
            # 2.5 检测用户内容是否违规
            # user_input_check_result = await self.ethics_service.check(content)
            # # result 是一个元组 (is_safe, issue_type, safe_response)
            # is_safe = user_input_check_result[0]
            # issue_type = user_input_check_result[1]
            # safe_response = user_input_check_result[2]
            # if not is_safe:
            #     # 用户输入违规，返回建议回复
            #     yield safe_response
            #     return

            # 3. 获取历史消息
            # recent_history = await self.message_repo.get_messages_page(
            #     conversation.id,
            #     PageParams(page=1, page_size=10)
            # )
            logger.info(f"最近几条历史消息：{recent_history}")

            # 4. 构建消息历史
            message_history = [
                {
                    "role": "user" if msg.sender_type == "user" else "assistant",
                    "content": msg.content
                }
                for msg in recent_history
            ]
            # 4.5 构建历史消息摘要
            # 获取用户与该角色的对话次数，如果对话次数较多，将历史对话内容输入到大模型中，生成精炼的历史记录摘要
            # 该操作的条件为对话次数超过50次，之后每增加40次对话就更新一次历史记录摘要
            # 历史记录摘要和历史消息不重复，历史记录摘要是对久远的历史消息的总结，而历史消息是近期20条的对话内容

            # history_summary = await  self.conversation_service.get_history_summary(conversation.id, user_id,  character_id)
            logger.info(f"历史记录摘要：{history_summary}")
            # 5. 构建提示词
            messages_for_llm = await build_system_prompt(character, content, message_history, history_summary)
            logger.info(f"content: {content}")
            # 6. 流式生成回复 - 这部分可能失败

            try:
                async with self._llm_semaphore:
                    async for token in chat_completion_stream(messages_for_llm):
                        reply_buffer += token
                        yield token
                # =====================
                # async with self.__class__._llm_semaphore:
                #     async for token in chat_completion_stream(messages_for_llm):
                #         reply_buffer += token
                #         yield token
                #         =================
                # async for token in deepseek_chat_stream(messages_for_llm):
                #     reply_buffer += token
                #     yield token
                logger.info(f"LLM流式生成完成，回复内容：{reply_buffer}")

                # ✅ 发送结束标记

                # 6.5 检测生成内容是否违规,在生成完成后检测
                is_safe, issue_type, _ = await ethics_service.check(reply_buffer)

                if not is_safe:
                    logger.warning(f"AI回复违规: {issue_type}")
                    # 发送一个特殊标记，让前端替换内容
                    yield "\n\n[REPLACE_LAST]抱歉，我无法回答这个问题。"
                    reply_buffer = "抱歉，我无法回答这个问题。"

                yield "[DONE]"
                stream_success = True
                # ✅ 流式完成后，触发异步摘要更新
                # asyncio.create_task(
                #     self.conversation_service.check_and_update_summary(
                #         conversation.id, user_id, character_id
                #     )
                # )
            except Exception as e:
                logger.error(f"LLM流式生成失败: {e}")
                # 生成错误信息给客户端
                error_msg = f"\n\n[流式回复系统错误: {str(e)}]"
                yield error_msg
                # 这里不重新抛出异常，让流程继续但跳过保存
                # 但需要确保回滚
                # await self.db.rollback()
                return  # 直接返回，不执行后续保存

            # # 7. 只有在流式成功时才保存消息
            # if stream_success:
            #     # 保存用户消息
            #     await self.message_repo.create(
            #         conversation_id=conversation.id,
            #         sender_type="user",
            #         content=content,
            #         token_count=-1
            #     )
            #
            #     # 保存助手消息
            #     await self.message_repo.create(
            #         conversation_id=conversation.id,
            #         sender_type="assistant",
            #         content=reply_buffer,
            #         token_count=-1
            #     )
            #
            #     await self.conversation_repo.touch(conversation)
            #
            #     # ✅ 更新 message_count（在保存消息后）
            #     conversation.message_count = (conversation.message_count or 0) + 2
            #     self.db.add(conversation)
            #
            #     # 提交事务
            #     await self.db.commit()
            #     logger.info("消息保存成功")
            #
            #     # # 记录统计
            #     # try:
            #     #     behavior_service = BehaviorService(self.db)
            #     #     await behavior_service.record_chat(user_id, character_id)
            #     #
            #     #     character_service = CharacterService(self.db)
            #     #     await character_service.increment_chat_count(character_id)
            #     #     await character_service.update_use_time(character_id)
            #     #
            #     #     await self.db.commit()
            #     #     logger.info("聊天统计记录成功")
            #     #
            #     # except Exception as e:
            #     #     # 出错时统一回滚
            #     #
            #     #     await self.db.rollback()
            #     #     logger.error(f"记录聊天统计失败: {e}")
            #
            #     # ✅ 这些可以并行执行，不阻塞主流程
            #     async def record_statistics():
            #         try:
            #             behavior_service = BehaviorService(self.db)
            #             await behavior_service.record_chat(user_id, character_id)
            #
            #             character_service = CharacterService(self.db)
            #             await character_service.increment_chat_count(character_id)
            #             await character_service.update_use_time(character_id)
            #
            #             await self.db.commit()
            #             logger.info("聊天统计记录成功")
            #         except Exception as e:
            #             logger.error(f"记录聊天统计失败: {e}")
            #             await self.db.rollback()
            #
            #     # 后台执行统计记录（不等待）
            #     asyncio.create_task(record_statistics())
            #
            #     # ==================== 摘要更新（后台任务） ====================
            #     # ✅ 检查是否需要更新摘要（不阻塞主流程）
            #     if conversation.message_count % 20 == 0:
            #         logger.info(f"触发摘要更新: message_count={conversation.message_count}")
            #         asyncio.create_task(
            #             self.conversation_service.update_summary(
            #                 conversation_id=conversation.id,
            #                 new_messages=recent_history,  # 传入已有的历史消息
            #                 existing_summary=history_summary  # 传入已有的摘要
            #             )
            #         )
            #
            # else:
            #     # 流式失败，确保回滚
            #
            #     await self.db.rollback()
            #     logger.warning("流式生成失败，未保存任何消息")

            # ✅ 所有数据库操作都放入后台任务
            asyncio.create_task(self._save_conversation_data(
                conversation_id=conversation.id,
                user_id=user_id,
                character_id=character_id,
                user_content=content,
                assistant_content=reply_buffer,
                recent_history=recent_history,
                history_summary=history_summary
            ))
            return
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            # 确保回滚
            if conversation:  # 只有有会话时才需要回滚
                await self.db.rollback()
            # 重新抛出，让上层处理
            raise

    async def _save_conversation_data(
            self,
            conversation_id:int,
            user_id: int,
            character_id: int,
            user_content: str,
            assistant_content: str,
            recent_history: list,
            history_summary: str
    ):
        """后台任务：保存消息、更新统计、更新摘要"""
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                message_repo = MessageRepository(db)
                conversation_repo = ConversationRepository(db)
                conversation = await conversation_repo.get_by_id(conversation_id)
                # 1. 保存用户消息
                await message_repo.create(
                    conversation_id=conversation.id,
                    sender_type="user",
                    content=user_content,
                    token_count=-1
                )

                # 2. 保存助手消息
                await message_repo.create(
                    conversation_id=conversation.id,
                    sender_type="assistant",
                    content=assistant_content,
                    token_count=-1
                )

                # 3. 更新会话时间
                await conversation_repo.touch(conversation)

                # 4. 更新消息计数
                conversation.message_count = (conversation.message_count or 0) + 2
                db.add(conversation)

                await db.commit()
                logger.info(f"消息保存成功: conversation_id={conversation.id}")

                # 5. 记录统计
                behavior_service = BehaviorService(db)
                await behavior_service.record_chat(user_id, character_id)

                character_service = CharacterService(db)
                await character_service.increment_chat_count(character_id)
                await character_service.update_use_time(character_id)

                await db.commit()
                logger.info("聊天统计记录成功")

                # 6. 摘要更新
                if conversation.message_count and conversation.message_count % 20 == 0:
                    logger.info(f"触发摘要更新: message_count={conversation.message_count}")
                    conv_service = ConversationService(db)
                    await conv_service.update_summary(
                        conversation_id=conversation.id,
                        new_messages=recent_history,
                        existing_summary=history_summary
                    )

            except Exception as e:
                logger.error(f"后台保存数据失败: {e}")
                await db.rollback()

