from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.voice import Voice


class VoiceRepository:

    def __init__(self, db: AsyncSession):
        self.db = db
    async def save_voice(self,voice_id, voice_name, voice_text, voice_url, duration, user_id):

        voice = Voice(
            voice_id=voice_id,
            voice_name=voice_name,
            voice_text=voice_text,
            voice_url=voice_url,
            duration=duration,
            user_id=user_id
        )

        self.db.add(voice)
        await self.db.flush()
        await self.db.refresh(voice)
        return voice


    async def list_voices(self,skip, limit):
        """获取所有声音"""
        stmt = select(Voice).order_by(Voice.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_voice_by_id(self, voice_id):
        stmt = select(Voice).where(Voice.voice_id == voice_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_voices_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> List[Voice]:
        """获取用户的所有声音"""
        stmt = select(Voice).where(
            Voice.user_id == user_id
        ).order_by(Voice.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()


    # @staticmethod
    # def create_voice(voice_name: str, voice_text: str, voice_wav_url: str,
    #                  duration: float, description: str = "") -> Voice:
    #     """创建新声音记录"""
    #     db = Session()
    #     try:
    #         voice = Voice(
    #             voice_name=voice_name,
    #             voice_text=voice_text,
    #             voice_wav_url=voice_wav_url,
    #             duration=duration,
    #             description=description
    #         )
    #         db.add(voice)
    #         db.commit()
    #         db.refresh(voice)
    #         return voice
    #     finally:
    #         db.close()
    #
    # @staticmethod
    # def get_voice(voice_id: str) -> Optional[Voice]:
    #     """获取声音信息"""
    #     db = SessionLocal()
    #     try:
    #         return db.query(Voice).filter(Voice.voice_id == voice_id).first()
    #     finally:
    #         db.close()
    #
    # @staticmethod
    # def list_voices(skip: int = 0, limit: int = 100) -> List[Voice]:
    #     """列出所有声音"""
    #     db = SessionLocal()
    #     try:
    #         return db.query(Voice).offset(skip).limit(limit).all()
    #     finally:
    #         db.close()
    #
    # @staticmethod
    # def delete_voice(voice_id: str) -> bool:
    #     """删除声音"""
    #     db = SessionLocal()
    #     try:
    #         voice = db.query(Voice).filter(Voice.voice_id == voice_id).first()
    #         if voice:
    #             # 删除对应的音频文件
    #             if os.path.exists(voice.voice_wav_url):
    #                 os.remove(voice.voice_wav_url)
    #             db.delete(voice)
    #             db.commit()
    #             return True
    #         return False
    #     finally:
    #         db.close()
    #
    # # class GeneratedAudioDB:
    # """生成音频记录操作"""
    #
    # @staticmethod
    # def create_record(voice_id: str, source_text: str, audio_url: str, duration: float) -> GeneratedAudio:
    #     db = SessionLocal()
    #     try:
    #         record = GeneratedAudio(
    #             voice_id=voice_id,
    #             source_text=source_text,
    #             audio_url=audio_url,
    #             duration=duration
    #         )
    #         db.add(record)
    #         db.commit()
    #         db.refresh(record)
    #         return record
    #     finally:
    #         db.close()
    #
    # @staticmethod
    # def list_by_voice(voice_id: str) -> List[GeneratedAudio]:
    #     """查询某个声音生成的所有音频"""
    #     db = SessionLocal()
    #     try:
    #         return db.query(GeneratedAudio).filter(
    #             GeneratedAudio.voice_id == voice_id
    #         ).order_by(GeneratedAudio.created_at.desc()).all()
    #     finally:
    #         db.close()
    #
