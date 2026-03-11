from typing import Optional, List, Dict

from pydantic import BaseModel


class CharacterLikeCount(BaseModel):
    character_id: int
    like_count: int



class CharacterLike(BaseModel):
    character_id: int
    like_count: int
    is_liked: Optional[bool] = None


class LikeStatusRequest(BaseModel):
    character_id: int


class LikeStatusResponse(BaseModel):
    liked_map: Dict[int, bool]



class BatchLikeStatusRequest(BaseModel):
    character_ids: List[int]


class BatchLikeStatusResponse(BaseModel):
    liked_map: Dict[int, bool]