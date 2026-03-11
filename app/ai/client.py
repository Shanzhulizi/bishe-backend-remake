from typing import List, Dict

from app.ai.local_model import local_model_chat, local_model_chat_stream
from app.ai.schemas import LLMResponse


async def chat_completion(messages: List[Dict]) -> LLMResponse:
    # 后期可以根据配置切换不同模型
    # return await deepseek_chat(messages)

    return await local_model_chat(messages)

async def chat_completion_stream(messages):
    try:
        async for token in local_model_chat_stream(messages):
            yield token
    except Exception as e:
        print(f"chat_completion_stream 错误: {e}")
        yield f"错误: {str(e)}"
