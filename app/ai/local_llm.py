# # app/ai/local_llm.py
# import asyncio
# import concurrent.futures
# import ollama
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# class LocalLLM:
#     """本地 Ollama 调用器（只负责调用，不关心业务）"""
#
#     _executor = None
#     _semaphore = asyncio.Semaphore(3)  # 本地模型并发限制
#
#     @classmethod
#     def _get_executor(cls):
#         if cls._executor is None:
#             cls._executor = concu
#             rrent.futures.ThreadPoolExecutor(max_workers=3)
#         return cls._executor
#
#     @classmethod
#     async def chat(cls, messages: list, model: str = "qwen2.5:3b", **options) -> str:
#         """异步调用本地 Ollama"""
#         async with cls._semaphore:
#             executor = cls._get_executor()
#
#             def _sync_call():
#                 try:
#                     resp = ollama.chat(
#                         model=model,
#                         messages=messages,
#                         stream=False,
#                         options={
#                             "temperature": options.get("temperature", 0.3),
#                             "num_predict": options.get("num_predict", 100),
#                             **options
#                         }
#                     )
#                     return resp["message"]["content"]
#                 except Exception as e:
#                     logger.error(f"Ollama 调用失败: {e}")
#                     return None
#
#             loop = asyncio.get_event_loop()
#             return await loop.run_in_executor(executor, _sync_call)





import asyncio
import concurrent.futures
from typing import Dict, Tuple, Optional
import ollama
import logging

logger = logging.getLogger(__name__)


# ==============================================
# 情感分析专用 LLM 调用器（完全独立）
# ==============================================
class SentimentLocalLLM:
    _executor = None
    _semaphore = asyncio.Semaphore(2)  # 情感分析独立并发限制

    @classmethod
    def _get_executor(cls):
        if cls._executor is None:
            cls._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        return cls._executor

    @classmethod
    async def chat(cls, messages: list, model: str = "qwen2.5:1.5b", **options) -> str:
        async with cls._semaphore:
            executor = cls._get_executor()

            def _sync_call():
                try:
                    resp = ollama.chat(
                        model=model,
                        messages=messages,
                        stream=False,
                        options={
                            "temperature": options.get("temperature", 0.1),
                            "num_predict": options.get("num_predict", 80),
                            **options
                        }
                    )
                    return resp["message"]["content"]
                except Exception as e:
                    logger.error(f"情感模型调用失败: {e}")
                    return None

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(executor, _sync_call)


# ==============================================
# 内容安全审核专用 LLM 调用器（完全独立）
# ==============================================
class SafetyLocalLLM:
    _executor = None
    _semaphore = asyncio.Semaphore(2)  # 审核独立并发限制

    @classmethod
    def _get_executor(cls):
        if cls._executor is None:
            cls._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        return cls._executor

    @classmethod
    async def chat(cls, messages: list, model: str = "qwen2.5:3b", **options) -> str:
        async with cls._semaphore:
            executor = cls._get_executor()

            def _sync_call():
                try:
                    resp = ollama.chat(
                        model=model,
                        messages=messages,
                        stream=False,
                        options={
                            "temperature": options.get("temperature", 0.3),
                            "num_predict": options.get("num_predict", 80),
                            **options
                        }
                    )
                    return resp["message"]["content"]
                except Exception as e:
                    logger.error(f"审核模型调用失败: {e}")
                    return None

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(executor, _sync_call)

