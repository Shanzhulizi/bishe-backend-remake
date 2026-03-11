"""
    对接DeepSeek API

"""

from typing import List, Dict

import httpx

from app.ai.schemas import LLMResponse, LLMUsage
from app.core.config import settings


async def deepseek_chat(messages: List[Dict]) -> LLMResponse:
    payload = {
        "models": settings.DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:

            resp = await client.post(
                settings.DEEPSEEK_BASE_URL,
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            choice = data["choices"][0]
            usage = data.get("usage")

            return LLMResponse(
                reply=choice["message"]["content"],
                usage=LLMUsage(**usage) if usage else None,
                finish_reason=choice.get("finish_reason"),
            )
        except httpx.TimeoutException:
            raise Exception("API请求超时")
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail.get('message', str(error_detail))}"
            except:
                pass
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")
