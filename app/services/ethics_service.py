import asyncio
from typing import Tuple, Optional

import ollama

from app.ai.local_llm import  SafetyLocalLLM
from app.core.logging import get_logger

logger = get_logger(__name__)


class EthicsService:
    def __init__(self, model: str = "qwen2.5:3b"):
        self.model = model

        # 快速黑名单
        self._blacklist = [
            '杀人', '自杀', '自残', '吸毒', '毒品', '色情',
            '淫秽', '血腥', '暴力'
        ]

    async def check(self, text: str) -> Tuple[bool, str, Optional[str]]:
        """安全检测"""
        # 1. 快速关键词过滤
        # for kw in self._blacklist:
        #     if kw in text:
        #         logger.warning(f"命中敏感词: {kw}")
        #         return False, "违规", "请勿发送不当内容"

        # 2. 检查缓存
        # cache_key = hashlib.md5(text.encode()).hexdigest()
        # if cache_key in self._cache:
        #     return self._cache[cache_key]

        # 3. 调用本地模型
        result = await self._call_llm(text)
        # self._cache[cache_key] = result
        return result

    async def _call_llm(self, text: str) -> Tuple[bool, str, Optional[str]]:
        """调用本地模型"""
        prompt = f"""你是内容安全审核员，判断文本是否违规，只对较为严重的违规内容视为违规，只返回JSON：{{"safe":true/false,"type":"违规类型","reply":"建议回复"}}

        文本内容：{text}"""

        messages = [
            {"role": "system", "content": "你是安全审核员，判断内容是否违规，只对较为严重的违规内容视为违规。只返回JSON。"},
            {"role": "user", "content": prompt}
        ]

        response = await SafetyLocalLLM.chat(
            messages=messages,
            model=self.model,
            temperature=0.3,
            num_predict=80
        )

        return self._parse_response(response or '{"safe":true}')

    def _parse_response(self, text: str) -> Tuple[bool, str, Optional[str]]:
        try:
            import json
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0:
                data = json.loads(text[start:end])
                return data.get('safe', True), data.get('type', '安全'), data.get('reply')
        except:
            pass
        return True, '安全', None


ethics_service = EthicsService()

