from app.ai.local_model import local_model_summary
from app.core.logging import get_logger
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.page import PageParams
from app.services.message_service import MessageService

logger = get_logger(__name__)


class ConversationService:
    def __init__(self, db):
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.message_service = MessageService(db)

    async def get_conv(self, user_id, character_id):
        conv = await self.conv_repo.get_active(user_id=user_id, character_id=character_id)
        return conv

    async def create_conv(self, user_id, character_id):
        conv = await self.conv_repo.create(user_id=user_id, character_id=character_id)
        return conv

    async def build_history_summary(self, conversation_id,  user_id, character_id) -> str:

        # 获取现有总结和已总结数量
        existing_summary = self.conv_repo.get_summary(user_id, character_id)
        summarized_count = self.conv_repo.get_summary_count(conversation_id)

        # 获取当前对话的消息总数
        chat_count = await self.conv_repo.get_chat_count(user_id, character_id)

        # 未总结的消息数
        unsummarized_count = chat_count - summarized_count

        # 定义阈值和总结数量
        FIRST_SUMMARY_THRESHOLD = 40  # 首次总结阈值（达到40条才总结）
        FIRST_SUMMARY_COUNT = 20  # 首次总结消息数（只总结前20条）
        INCREMENTAL_THRESHOLD = 20  # 增量总结阈值（新增20条新消息）
        INCREMENTAL_COUNT = 20  # 增量总结消息数（每次总结20条）

        # 判断是否需要总结
        should_summarize = False
        new_messages = []

        if summarized_count == 0:
            # 首次总结：消息数达到40条
            if chat_count >= FIRST_SUMMARY_THRESHOLD:
                should_summarize = True
                # 取第1页，20条（只总结前20条）
                new_messages = self.message_service.get_history_messages(
                    conversation_id,
                    PageParams(page=2, page_size=FIRST_SUMMARY_COUNT)
                )
                new_summarized_count = FIRST_SUMMARY_COUNT

        elif unsummarized_count >= INCREMENTAL_THRESHOLD:
            # 增量总结：新消息达到20条
            should_summarize = True
            # 计算页码：已总结数量 ÷ 每页数量 + 1
            # 假设每页20条，已总结20条，则取第2页
            # page = (summarized_count // INCREMENTAL_COUNT) + 1

            new_messages = self.message_service.get_history_messages(
                conversation_id,
                PageParams(page=2, page_size=INCREMENTAL_COUNT)
            )

            new_summarized_count = summarized_count + len(new_messages)

        if not should_summarize or not new_messages:
            return existing_summary or "无"

        # 生成总结
        if summarized_count == 0:
            new_summary = await local_model_summary(new_messages)
        else:
            new_summary = await local_model_summary(new_messages, existing_summary)

        # 保存总结
        self.conv_repo.save_summary(
            conversation_id=conversation_id,
            summary=new_summary,
            summarized_count=new_summarized_count
        )

        return new_summary or "无"





        # if summarized_count == 0:
        #     # 如果没有历史总结,直接将历史记录输入到模型中进行总结
        #     logger.info(f"首次构建历史总结，conversation_id={conversation_id}, chat_count={chat_count}")
        #     history = self.message_service.get_history_messages(conversation_id, PageParams(page=1, page_size=50))
        #     history_summary = await local_model_summary(history)
        #     summary_count = 50
        #     # self.conv_repo.save_summary_count(summary_count, conversation_id)
        # elif chat_count > 50 and (chat_count - 50) % 40 == 0:
        #     #     获取未总结的40条消息中的前20条加入历史总结中进行新的总结
        #     logger.info(f"更新历史总结，conversation_id={conversation_id}, chat_count={chat_count}")
        #     history = self.message_service.get_history_messages(conversation_id, PageParams(page=2, page_size=20))
        #     history_summary = self.conv_repo.get_summary(user_id, character_id)
        #
        #     history_summary = await local_model_summary(history, history_summary)
        #     conv = await self.get_conv(user_id, character_id)
        #
        #     summary_count = conv.summary_count + 20
        # # 保存历史总结到数据库中
        # self.conv_repo.save_summary(conversation_id, history_summary, summary_count)
        # return history_summary if history_summary else "无"
