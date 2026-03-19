from pydantic import BaseModel

from .page import PageResponse


class MessageBase(BaseModel):
    """消息基础schema"""
    sender_type: str
    content: str
    # token_count: Optional[int] = None
    # in_context: Optional[bool] = True



class MessagePageResponse(PageResponse[MessageBase]):
    """消息分页响应"""
    pass  # 直接继承PageResponse，泛型指定为Message