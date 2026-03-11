from typing import Optional, Literal

from pydantic import BaseModel

"""
请求模型
"""


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    # , "system"    # system 永远不从前端接收

    content: str


class ChatRequest(BaseModel):
    character_id: int
    message: str
    # history: List[ChatMessage] = Field(default_factory=list)


"""
响应模型
"""


class ChatResponse(BaseModel):
    reply: str
    usage: Optional[dict] = None
    # 可以添加更多字段
    finish_reason: Optional[str] = None
