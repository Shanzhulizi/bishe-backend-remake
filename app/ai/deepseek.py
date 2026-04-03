"""
    对接DeepSeek API

"""

from typing import List, Dict

import httpx

from app.ai.schemas import LLMResponse, LLMUsage
from app.core.config import settings
from typing import AsyncGenerator, List, Dict
import httpx
import json


async def deepseek_chat_stream(messages: List[Dict]) :
    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": True,
    }

    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    # ✅ 增加超时时间：连接超时 10秒，读取超时 120秒
    timeout = httpx.Timeout(
        connect=10.0,      # 连接超时
        read=120.0,        # 读取超时（最重要，等待响应）
        write=30.0,        # 写入超时
        pool=5.0           # 连接池超时
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream(
                    "POST",
                    settings.DEEPSEEK_BASE_URL,
                    json=payload,
                    headers=headers,
            ) as response:
                response.raise_for_status()

                # ✅ 逐行读取流式响应
                async for line in response.aiter_lines():
                    # SSE 格式：data: {...}
                    if line.startswith("data: "):
                        data_str = line[6:]  # 去掉 "data: " 前缀

                        # 流结束标记
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            # 提取 content
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            # logger.warning(f"JSON 解析失败: {data_str}")
                            continue

        except httpx.TimeoutException:
            # logger.error("DeepSeek API 请求超时")
            yield "\n\n[系统错误: API请求超时]"
        except httpx.HTTPStatusError as e:
            # logger.error(f"DeepSeek API HTTP错误: {e}")
            error_msg = f"HTTP错误: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail.get('message', str(error_detail))}"
            except:
                pass
            yield f"\n\n[系统错误: {error_msg}]"
        except Exception as e:
            # logger.error(f"DeepSeek API 调用失败: {e}")
            yield f"\n\n[系统错误: {str(e)}]"



async def deepseek_chat(messages: List[Dict]) -> LLMResponse:
    payload = {
        "model": settings.DEEPSEEK_MODEL,
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
