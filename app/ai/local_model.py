"""
    对接本地模型
"""
from types import SimpleNamespace

import ollama

from app.core.logging import get_logger

# 添加日志
logger = get_logger(__name__)


# async def local_model_chat(messages: list) -> SimpleNamespace:  # 改为返回 SimpleNamespace
#     """
#     使用本地 Ollama 模型
#     messages: [{"role": "user", "content": "你好"}]
#     """
#     try:
#         # 正确的消息格式转换 - Ollama 需要的是 role/content 格式
#         ollama_messages = []
#         for msg in messages:
#             # 直接保留原有的 role/content 格式
#             ollama_messages.append({
#                 "role": msg["role"],  # "user" 或 "assistant"
#                 "content": msg["content"]
#             })
#
#         logger.info(f"发送到Ollama的消息: {ollama_messages}")
#
#         # 正确的 Ollama 调用方式
#         # 注意：temperature 和 max_tokens 要放在 options 里
#         resp = ollama.chat(
#             model="qwen2.5:7b",  # 确保这个模型已下载
#             messages=ollama_messages,
#             stream=False,
#             options={  # 参数放在这里！
#                 "temperature": 0.7,  # 温度参数
#                 "num_predict": 2000,  # max_tokens 对应 num_predict
#                 "top_k": 40,
#                 "top_p": 0.9,
#                 "repeat_penalty": 1.1
#             }
#         )
#
#         logger.info(f"本地模型的完整回复：{resp}")
#         # 提取回复内容 - Ollama 返回格式
#         if isinstance(resp, dict):
#             if "message" in resp:
#                 reply = resp["message"].get("content", "")
#             elif "response" in resp:
#                 reply = resp["response"]
#             else:
#                 reply = str(resp)
#         else:
#             reply = str(resp)
#
#         reply = resp["message"]["content"]
#         logger.info(f"Ollama回复: {reply[:100]}...")  # 只记录前100个字符
#
#         # 关键修改：返回对象而不是字典！
#         # 创建 SimpleNamespace 对象，这样就能用 .reply 和 .usage.total_tokens 访问
#         response = SimpleNamespace(
#             reply=reply,
#             usage=SimpleNamespace(
#                 total_tokens=-1 # 本地模型暂时不计算token
#             ),
#             finish_reason="stop"
#         )
#
#         return response  # 返回对象
#
#     except ollama.ResponseError as e:
#         logger.error(f"Ollama响应错误: {e.error}")
#         if "models not found" in str(e).lower():
#             raise Exception(f"模型 'qwen2.5' 未安装，请运行: ollama pull qwen2.5")
#         raise Exception(f"Ollama调用失败: {str(e)}")
#
#     except Exception as e:
#         logger.error(f"本地模型调用失败: {str(e)}")
#         raise Exception(f"本地模型调用失败: {str(e)}")

async def local_model_chat(messages: list) -> SimpleNamespace:
    """
    使用本地 Ollama 模型 - 异步版本
    """
    import asyncio
    from types import SimpleNamespace

    def _sync_chat():
        """同步版本的聊天调用"""
        try:
            ollama_messages = []
            for msg in messages:
                ollama_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            logger.info(f"发送到Ollama的消息: {ollama_messages}")

            resp = ollama.chat(
                model="qwen2.5:7b",
                messages=ollama_messages,
                stream=False,
                options={
                    "temperature": 0.7,
                    "num_predict": 2000,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            )

            logger.info(f"本地模型的完整回复：{resp}")

            if isinstance(resp, dict):
                if "message" in resp:
                    reply = resp["message"].get("content", "")
                elif "response" in resp:
                    reply = resp["response"]
                else:
                    reply = str(resp)
            else:
                reply = str(resp)

            return SimpleNamespace(
                reply=reply,
                usage=SimpleNamespace(total_tokens=-1),
                finish_reason="stop"
            )

        except ollama.ResponseError as e:
            logger.error(f"Ollama响应错误: {e.error}")
            if "models not found" in str(e).lower():
                raise Exception(f"模型 'qwen2.5' 未安装，请运行: ollama pull qwen2.5")
            raise Exception(f"Ollama调用失败: {str(e)}")
        except Exception as e:
            logger.error(f"本地模型调用失败: {str(e)}")
            raise Exception(f"本地模型调用失败: {str(e)}")

    # 在线程池中运行同步函数
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_chat)



async def local_model_chat_stream(messages: list):
    """
    流式生成回复 - 使用线程池执行同步的 ollama 调用
    """
    import asyncio
    import queue
    from threading import Thread

    # 创建一个队列来传递数据
    result_queue = queue.Queue()

    def _sync_stream():
        """同步版本的流式调用，在线程中运行"""
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
                    "num_predict": 500,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            )

            for chunk in stream:
                if "message" in chunk:
                    token = chunk["message"]["content"]
                    if token:
                        result_queue.put(("token", token))
            result_queue.put(("done", None))

        except Exception as e:
            logger.error(f"Ollama流式输出错误: {e}")
            result_queue.put(("error", str(e)))

    # 在线程中运行同步函数
    loop = asyncio.get_event_loop()
    thread = Thread(target=_sync_stream)
    thread.start()

    # 异步地从队列中获取数据
    while True:
        try:
            # 非阻塞地检查队列
            item_type, data = await loop.run_in_executor(None, result_queue.get, True, 0.1)

            if item_type == "token":
                yield data
            elif item_type == "done":
                break
            elif item_type == "error":
                raise Exception(data)
        except queue.Empty:
            await asyncio.sleep(0.01)
            continue





async def local_model_summary(history: list, history_summary: str = ""):
    """异步生成对话摘要"""
    import asyncio

    def _sync_summary():
        """同步版本摘要生成"""
        try:
            # 1. 格式化消息列表
            formatted_messages = []
            for msg in history:
                if msg.sender_type == "user":
                    role = "用户"
                elif msg.sender_type == "assistant":
                    role = "助手"
                else:
                    role = "系统"
                formatted_messages.append(f"{role}: {msg.content}")

            conversation_text = "\n".join(formatted_messages)

            # 2. 构建提示词
            if history_summary:
                prompt = f"""请根据以下已有的对话摘要和新对话内容，生成一份更新后的完整摘要。

                    【已有摘要】
                    {history_summary}

                    【新对话内容】
                    {conversation_text}

                    【要求】
                    1. 保持摘要简洁，突出重点信息
                    2. 如果新对话是旧话题的延续，合并到对应话题中
                    3. 如果出现新话题，添加到摘要中
                    4. 提取对话中的关键信息和主要话题
                    5. 摘要控制在100字以内
                    【更新后的摘要】
                    """
            else:
                prompt = f"""请总结以下对话的核心内容。

                    【对话内容】
                    {conversation_text}

                    【要求】
                    1. 提取对话中的关键信息和主要话题
                    2. 总结用户的核心诉求和助手的回应
                    3. 摘要要简洁明了，控制在150字以内

                    【摘要】
                    """

            response = ollama.chat(
                model="qwen2.5:7b",
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.3,
                    "num_predict": 300
                }
            )

            return response["message"]["content"]

        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return "对话摘要生成失败"

    # 在线程池中运行同步函数
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _sync_summary)
    logger.info(f"对话历史生成摘要：{result}")
    return result

