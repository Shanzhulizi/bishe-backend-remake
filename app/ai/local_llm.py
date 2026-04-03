# app/ai/local_llm.py
import asyncio
import concurrent.futures
import ollama
import logging

logger = logging.getLogger(__name__)


class LocalLLM:
    """本地 Ollama 调用器（只负责调用，不关心业务）"""

    _executor = None
    _semaphore = asyncio.Semaphore(3)  # 本地模型并发限制

    @classmethod
    def _get_executor(cls):
        if cls._executor is None:
            cls._executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        return cls._executor

    @classmethod
    async def chat(cls, messages: list, model: str = "qwen2.5:3b", **options) -> str:
        """异步调用本地 Ollama"""
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
                            "num_predict": options.get("num_predict", 100),
                            **options
                        }
                    )
                    return resp["message"]["content"]
                except Exception as e:
                    logger.error(f"Ollama 调用失败: {e}")
                    return None

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(executor, _sync_call)