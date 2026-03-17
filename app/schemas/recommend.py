from typing import Optional

from pydantic import BaseModel

from pydantic import BaseModel
from typing import List, Optional
from app.schemas.character import CharacterListItem


class RecommendResponse(BaseModel):
    """推荐响应"""
    code: int = 200
    msg: str = "success"
    data: List[CharacterListItem] = []
    total: int = 0
    scene: str = ""  # 推荐场景: home/personal/detail
