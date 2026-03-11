from typing import Optional

from pydantic import BaseModel


class LLMUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(BaseModel):
    reply: str
    usage: Optional[LLMUsage] = None
    finish_reason: Optional[str] = None
