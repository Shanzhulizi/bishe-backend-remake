from typing import Optional

from pydantic import BaseModel


class ASRResponse(BaseModel):
    text: str
    duration: float


class TTSRequest(BaseModel):
    text: str
    # character_id: int
    # voice_style: str = "default"
    voice_code: Optional[str] = None  # 可选的声音代码


class TTSResponse(BaseModel):
    audio_url: str
