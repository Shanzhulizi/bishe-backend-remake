from typing import Tuple, Optional

from app.ai.local_model import local_model_check
from app.core.logging import get_logger

logger = get_logger(__name__)


class EthicsService:
    def __init__(self, model: str = "qwen2.5:3b"):
        self.model = model

    async def check(self, text: str) -> Tuple[bool, str, Optional[str]]:
        ai_result = await local_model_check(text=text)
        return self._parse_result(ai_result)

    def _parse_result(self, result: str) -> Tuple[bool, str, Optional[str]]:
        """解析LLM返回结果"""
        is_safe = "安全：是" in result
        issue_type = "安全"
        safe_response = None

        for line in result.split('\n'):
            if "类型：" in line:
                issue_type = line.split("：")[-1].strip()
            if "建议回复：" in line:
                safe_response = line.split("：")[-1].strip()

        return is_safe, issue_type, safe_response
