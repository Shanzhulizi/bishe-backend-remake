from sqlalchemy.orm import Session

from app.ai.client import chat_completion, chat_completion_stream
from app.ai.prompt_builder import build_system_prompt
from app.core.logging import get_logger
from app.repositories.character_repo import CharacterRepository
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.services.character_stat_service import CharacterStatService

logger = get_logger(__name__)


class ChatService:
    @staticmethod
    async def send_message(
            db: Session,
            user_id: int,
            character_id: int,
            content: str,

    ) -> str:
        logger.info(f"消息：{content}")
        try:
            # 获取或创建会话
            conversation = await ConversationRepository.get_active(
                db, user_id, character_id
            )
            if not conversation:
                conversation = await ConversationRepository.create(
                    db, user_id, character_id
                )

            # 准备消息历史记录（最近 N 条）
            history_msgs = await MessageRepository.get_messages_by_conversation(
                db, conversation.id
            )
            logger.info(f"完整历史消息：{history_msgs}")
            # 限制历史长度
            max_history = 10
            # 这句话的作用是 裁剪历史消息的长度，保证传给 LLM 的上下文不会太长
            recent_history = history_msgs[-max_history:] if len(history_msgs) > max_history else history_msgs

            logger.info(f"切割后的历史消息：{recent_history}")
            message_history = [
                {
                    "role": "user" if msg.sender_type == "user" else "assistant",
                    "content": msg.content
                }
                for msg in recent_history
            ]



            # 4️⃣ 构建 system prompt + 历史
            character = CharacterRepository.get_by_id(db, character_id)
            messages_for_llm = build_system_prompt(character, content, message_history)
            logger.info(f"Messages for LLM: {messages_for_llm}")
            # 4️⃣ 调用 LLM
            llm_resp = await chat_completion(messages_for_llm)

            reply = llm_resp.reply
            token_count = llm_resp.usage.total_tokens

            # 到这里才开始真正写库（事务安全）
            # 存储用户消息
            await MessageRepository.create(
                db,
                conversation_id=conversation.id,
                sender_type="user",
                content=content
            )
            # 存储助手回复
            assistant_message = await MessageRepository.create(
                db,
                conversation_id=conversation.id,
                sender_type="assistant",
                content=reply,
                token_count=token_count
            )

            # 更新会话的最后消息时间
            await ConversationRepository.touch(db, conversation)

            db.commit()
            return reply

        except Exception as e:
            db.rollback()
            # 记录日志（非常重要）
            logger.exception("send_message failed", exc_info=e)
            raise

    @staticmethod
    async def send_message_stream(
            db: Session,
            user_id: int,
            character_id: int,
            content: str,
    ):

        reply_buffer = ""

        # 获取或创建会话
        conversation = await ConversationRepository.get_active(
            db, user_id, character_id
        )
        if not conversation:
            conversation = await ConversationRepository.create(
                db, user_id, character_id
            )

        # 准备消息历史记录（最近 N 条）
        history_msgs = await MessageRepository.get_messages_by_conversation(
            db, conversation.id
        )
        history_msgs.reverse()
        for msg in history_msgs:
            logger.info(f"历史消息：{msg.sender_type} - {msg.content}")
        # logger.info(f"完整历史消息：{history_msgs}")
        # 限制历史长度
        max_history = 20
        # 这句话的作用是 裁剪历史消息的长度，保证传给 LLM 的上下文不会太长
        recent_history = history_msgs[-max_history:] if len(history_msgs) > max_history else history_msgs

        # logger.info(f"切割后的历史消息：{recent_history}")
        for msg in recent_history:
            logger.info(f"切割后的历史消息：{msg.sender_type} - {msg.content}")

        message_history = [
            {
                "role": "user" if msg.sender_type == "user" else "assistant",
                "content": msg.content
            }
            for msg in recent_history
        ]

        # 4️⃣ 构建 system prompt + 历史
        character = CharacterRepository.get_by_id(db, character_id)
        messages_for_llm = build_system_prompt(character, content, message_history)
        logger.info(f"提示词：{messages_for_llm}")
        try:
            async for token in chat_completion_stream(messages_for_llm):
                reply_buffer += token

                yield token
        finally:
            # ===== 流结束之后 =====
            try:
                await MessageRepository.create(
                    db,
                    conversation_id=conversation.id,
                    sender_type="user",
                    content=content
                )

                await MessageRepository.create(
                    db,
                    conversation_id=conversation.id,
                    sender_type="assistant",
                    content=reply_buffer,
                    token_count=-1
                )
                await ConversationRepository.touch(db, conversation)

                db.commit()

                # 为推荐算法记录对话数据
                # TODO 为推荐算法记录对话数据
                CharacterStatService.record_chat(db, character_id, user_id)
            except Exception as e:
                print(f"保存消息失败: {e}")
                db.rollback()