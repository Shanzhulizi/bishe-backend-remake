from typing import Optional

from pydantic import BaseModel














class GenerateRequest(BaseModel):
    voice_id: str
    text: str