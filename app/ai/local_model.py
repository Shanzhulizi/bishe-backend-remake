"""
    对接本地模型
"""
from types import SimpleNamespace

import ollama

from app.core.logging import get_logger

# 添加日志
logger = get_logger(__name__)


async def local_model_chat(messages: list) -> SimpleNamespace:  # 改为返回 SimpleNamespace
    """
    使用本地 Ollama 模型
    messages: [{"role": "user", "content": "你好"}]
    """
    try:
        # 正确的消息格式转换 - Ollama 需要的是 role/content 格式
        ollama_messages = []
        for msg in messages:
            # 直接保留原有的 role/content 格式
            ollama_messages.append({
                "role": msg["role"],  # "user" 或 "assistant"
                "content": msg["content"]
            })

        logger.info(f"发送到Ollama的消息: {ollama_messages}")

        # 正确的 Ollama 调用方式
        # 注意：temperature 和 max_tokens 要放在 options 里
        resp = ollama.chat(
            model="qwen2.5:7b",  # 确保这个模型已下载
            messages=ollama_messages,
            stream=False,
            options={  # 参数放在这里！
                "temperature": 0.7,  # 温度参数
                "num_predict": 2000,  # max_tokens 对应 num_predict
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        )

        logger.info(f"本地模型的完整回复：{resp}")
        # 提取回复内容 - Ollama 返回格式
        if isinstance(resp, dict):
            if "message" in resp:
                reply = resp["message"].get("content", "")
            elif "response" in resp:
                reply = resp["response"]
            else:
                reply = str(resp)
        else:
            reply = str(resp)

        reply = resp["message"]["content"]
        logger.info(f"Ollama回复: {reply[:100]}...")  # 只记录前100个字符

        # 关键修改：返回对象而不是字典！
        # 创建 SimpleNamespace 对象，这样就能用 .reply 和 .usage.total_tokens 访问
        response = SimpleNamespace(
            reply=reply,
            usage=SimpleNamespace(
                total_tokens=-1 # 本地模型暂时不计算token
            ),
            finish_reason="stop"
        )

        return response  # 返回对象

    except ollama.ResponseError as e:
        logger.error(f"Ollama响应错误: {e.error}")
        if "models not found" in str(e).lower():
            raise Exception(f"模型 'qwen2.5' 未安装，请运行: ollama pull qwen2.5")
        raise Exception(f"Ollama调用失败: {str(e)}")

    except Exception as e:
        logger.error(f"本地模型调用失败: {str(e)}")
        raise Exception(f"本地模型调用失败: {str(e)}")


async def local_model_chat_stream(messages: list):
    try:
        ollama_messages = [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in messages
        ]

        stream = ollama.chat(
            model="qwen2.5:7b",
            messages=ollama_messages,
            stream=True,
            options={
                "temperature": 0.7,
                "num_predict": 2000,
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        )

        chunk_count = 0
        for chunk in stream:
            chunk_count += 1
            if "message" in chunk:
                token = chunk["message"]["content"]
                # print(f"发送第{chunk_count}个chunk: {token[:20]}...")
                if token:
                    yield token

    except Exception as e:
        print(f"Ollama流式输出错误: {e}")
        import traceback
        traceback.print_exc()
        yield f"【系统错误】{str(e)}"