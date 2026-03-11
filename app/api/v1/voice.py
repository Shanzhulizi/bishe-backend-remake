import shutil
import uuid
from pathlib import Path
from typing import List, Dict

import edge_tts
from fastapi import APIRouter, UploadFile, File, Form
from fastapi import Depends

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.constants import ResponseCode
from app.core.logging import get_logger
from app.schemas.common import ResponseModel
from app.schemas.voice import ASRResponse, TTSResponse, TTSRequest
from app.services.ars_service import ASRService
from app.services.tts_service import TTSService

# app/api/v1/voice.py

# router = APIRouter()
router = APIRouter()

logger = get_logger(__name__)

"""
    需要注意的是，这里的接口并不会在实际项目中直接使用，
    项目中的语音转文字和文本转语音功能会集成在聊天接口中。
    这里的接口仅作为示例，展示如何设计语音相关的 API。
    并且，这里也实现了具体的逻辑，可以更方便地测试单个功能
"""

"""
    语音转文字接口
"""


@router.post("/asr", response_model=ASRResponse)
async def voice_asr(
        audio: UploadFile = File(...),
        lang: str = "zh",
        user=Depends(get_current_user)
):
    audio_bytes = await audio.read()
    text, duration = await ASRService.speech_to_text(audio_bytes, lang)
    return {"text": text, "duration": duration}


"""
    文本转语音接口
"""


@router.post("/tts")
async def voice_tts(
        req: TTSRequest
):
    try:
        logger.info("开始生成语音")
        text = req.text
        voice_code = req.voice_code
        # 如果没有声音代码，使用默认
        if not voice_code:
            # 从数据库获取默认声音，或者使用硬编码默认值

            voice_code = "zh-CN-XiaoxiaoNeural"

            logger.info(f"使用默认声音: {voice_code}")

        audio_url = await TTSService.text_to_speech(
            text=text,
            voice_code=voice_code
        )
        logger.info(f"生成语音成功，URL: {audio_url}")
        return ResponseModel.success(msg="语音生成成功", data=TTSResponse(audio_url=audio_url)
                                     )
    except Exception as e:
        logger.error(f"生成语音失败: {e}")
        return ResponseModel.error(code=ResponseCode.INTERNAL_ERROR, msg="语音生成失败")


@router.get("/chinese")
async def get_chinese_voices() -> ResponseModel[List[Dict]]:
    """
    获取所有中文声音
    """
    logger.info("获取中文声音列表")
    try:
        # 获取所有声音
        voices = await edge_tts.list_voices()

        # 过滤出中文声音
        chinese_voices = []
        for voice in voices:
            locale = voice.get('Locale', '')
            if "CN" in locale:  # 中文
                chinese_voices.append({
                    "code": voice['ShortName'],
                    'name': voice['ShortName'],
                    # 'FriendlyName': voice['FriendlyName'],
                    "gender": voice['Gender'],
                    "locale": voice['Locale'],
                    "preview_text": "你好，我是你的AI助手，很高兴认识你。"
                })

        # 按性别和名称排序
        chinese_voices.sort(key=lambda x: (x['gender']
                                           , x['name']
                                           ))

        return ResponseModel.success(
            msg="获取中文声音成功",
            data=chinese_voices
        )
    except Exception as e:
        logger.error(f"获取中文声音失败: {e}")
        return ResponseModel.error(
            code=ResponseCode.INTERNAL_ERROR,
            msg=f"获取中文声音失败: {str(e)}"
        )


from app.core.config import settings


@router.get("/preview/{voice_code}")
async def preview_voice(voice_code: str) -> ResponseModel:
    """
    获取声音预览（生成试听音频）
    """
    logger.info(f"获取声音预览: {voice_code}")
    try:
        import edge_tts
        import hashlib
        from pathlib import Path

        local_host = settings.LOCAL_HOST
        static_dir = settings.STATIC_DIR
        preview_text = "你好，我是你的AI助手，很高兴认识你。"
        # 生成缓存key
        cache_key = hashlib.md5(f"{preview_text}_{voice_code}".encode()).hexdigest()

        # ✅ 使用 settings 中的 STATIC_DIR（这是项目根目录的 static）
        static_dir = Path(static_dir)  # 应该是 E:/Code/Python/AIChat/static
        preview_dir = static_dir / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        cache_file = preview_dir / f"{cache_key}.mp3"

        print(f"预览音频缓存路径: {cache_file}")  # 应该是 E:/Code/Python/AIChat/static/previews/xxx.mp3

        # 如果缓存不存在，生成音频
        if not cache_file.exists():
            communicate = edge_tts.Communicate(preview_text, voice_code)
            await communicate.save(str(cache_file))

        # 返回给前端的 URL
        audio_url = f"{local_host}/static/previews/{cache_key}.mp3"

        return ResponseModel.success(
            msg="获取预览成功",
            data={
                "audio_url": audio_url,
                "voice_code": voice_code
            }
        )
    except Exception as e:
        logger.error(f"生成预览失败: {e}")
        return ResponseModel.error(
            code=ResponseCode.INTERNAL_ERROR,
            msg=f"生成预览失败: {str(e)}"
        )

