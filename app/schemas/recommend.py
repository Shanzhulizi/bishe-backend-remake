from typing import List

from pydantic import BaseModel

from app.schemas.character import CharacterListItem


class RecommendResponse(BaseModel):
    """推荐响应"""
    code: int = 200
    msg: str = "success"
    data: List[CharacterListItem] = []
    total: int = 0
    scene: str = ""  # 推荐场景: home/personal/detail
