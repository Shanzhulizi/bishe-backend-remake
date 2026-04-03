from app.core.config import Settings

settings = Settings()

from app.core.logging import get_logger

logger = get_logger(__name__)


import uuid
from pathlib import Path
import soundfile as sf
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.voice_repo import VoiceRepository
class VoiceService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.voice_repo = VoiceRepository(db)
    async def save_voice(self, audio, voice_name, voice_text, user_id):
        suffix = Path(audio.filename).suffix
        logger.info(
            f"接收声音: voice_name={voice_name}, voice_text={voice_text}, filename={audio.filename}, suffix={suffix}")

        if not suffix or suffix not in [".wav", ".mp3"]:
            logger.warning(f"文件格式不支持，自动转为wav：{audio.filename}")
            raise ValueError("不支持的文件格式，请上传wav或mp3格式的音频")
        voice_id = "voice_" + uuid.uuid4().hex[:16]

        # voice_path = os.path.join(settings.COSYVOICE_SAMPLE_DIR, f"voice_id.wav")
        voice_path = settings.PROMPT_VOICE_DIR / f"{voice_id}{suffix}"
        voice_url = settings.LOCAL_HOST+  f"/static/voice/prompt_voice/{voice_id}{suffix}"
        voice_path.parent.mkdir(parents=True, exist_ok=True)
        with open(voice_path, "wb") as f:
            f.write(await audio.read())

        # 获取音频信息
        data, sr = sf.read(voice_path)
        duration = round(len(data) / sr, 2)
        logger.info(
            f"保存声音: voice_id={voice_id}, voice_name={voice_name}, voice_text={voice_text}, wav_path={voice_path}, duration={duration}, user_id={user_id}")

        await self.voice_repo.save_voice(voice_id, voice_name, voice_text, voice_url, duration, user_id)

        return {
            "voice_id": voice_id,
            "voice_url": voice_url,
            "duration": duration
        }

    async def get_all_voices(self, skip, limit):
        return await self.voice_repo.list_voices(skip, limit)

    async def get_voice_by_id(self, voice_id: str):
        """根据ID获取声音"""
        return await self.voice_repo.get_voice_by_id(voice_id)

    async def get_voices_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> list:
        """获取用户的所有声音"""
        return await self.voice_repo.get_voices_by_user(user_id, skip, limit)