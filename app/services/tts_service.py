import uuid
from pathlib import Path

import edge_tts

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
# 常用中文角色（可按 character 绑定）
VOICE_MAP = {
    "default": "zh-CN-XiaoxiaoNeural",
    "male": "zh-CN-YunxiNeural",
    "calm": "zh-CN-XiaoyiNeural",
}


#
# class TTSService:
#
#     @staticmethod
#     async def text_to_speech(
#             text: str,
#             character_id: int,
#             voice_style: str = "default"
#     ) -> str:
#         """
#         返回音频 URL
#         """
#         try:
#
#             voice = VOICE_MAP.get(voice_style, VOICE_MAP["default"])
#
#             filename = f"{uuid.uuid4().hex}.mp3"
#             save_dir = os.path.join(settings.AUDIO_FILES_DIR, "tts")
#
#             os.makedirs(save_dir, exist_ok=True)
#
#             file_path = os.path.join(save_dir, filename)
#
#             communicate = edge_tts.Communicate(
#                 text=text,
#                 voice=voice,
#                 rate="+0%",
#                 volume="+0%"
#             )
#
#             await communicate.save(file_path)
#
#             # return f"/static/tts/{filename}"
#             return f"http://localhost:8000/static/tts/{filename}"
#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             raise e


class TTSService:
    # 默认声音配置（备选）
    DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

    @staticmethod
    async def text_to_speech(
            text: str,
            voice_code: str,
            rate: str = "+0%",
            volume: str = "+0%",
            pitch: str = "+0Hz"
    ) :
        """
        文本转语音，返回音频URL

        Args:
            text: 要转换的文本
            voice_code: 声音代码（如：zh-CN-XiaoxiaoNeural）
            rate: 语速，如 "+10%", "-10%"
            volume: 音量，如 "+10%", "-10%"
            pitch: 音调，如 "+10Hz", "-10Hz"

        Returns:
            音频文件的URL
        """
        try:
            logger.info(f"TTS生成: voice_code={voice_code}, text='{text[:20]}...'")

            # 生成唯一文件名
            filename = f"{uuid.uuid4().hex}.mp3"

            # 确保保存目录存在
            save_dir = Path(settings.AUDIO_FILES_DIR) / "tts"
            save_dir.mkdir(parents=True, exist_ok=True)

            file_path = save_dir / filename

            # 创建 Edge TTS 通信对象
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_code,
                rate=rate,
                volume=volume,
                pitch=pitch
            )

            # 保存音频文件
            await communicate.save(str(file_path))

            logger.info(f"TTS生成成功: {filename}")

            # 返回URL
            # 开发环境
            return settings.AUDIO_FILES_DIR / filename
            # f"http://localhost:8000/static/tts/{filename}"

            # 生产环境（根据配置返回）
            # return f"{settings.API_BASE_URL}/static/tts/{filename}"

        except Exception as e:
            logger.error(f"TTS生成失败: {e}")
            import traceback
            traceback.print_exc()
            raise e

    @staticmethod
    async def get_voice_preview(voice_code: str) -> str:
        """
        获取声音预览（用固定文本）
        """
        preview_text = "你好，我是你的AI助手，很高兴认识你。"
        return await TTSService.text_to_speech(preview_text, voice_code)
