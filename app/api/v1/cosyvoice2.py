
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logging import get_logger

from app.models.user import User
from app.schemas.cosyvoice import GenerateRequest
from app.services.cosyvoice2_service import  cosyvoice2_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("/create")
async def create_voice(
        voice_name: str = Form(...),
        voice_text: str = Form(...),
        audio: UploadFile = File(...),
        current_user: User = Depends(get_current_user)
):
    try:
        voice_result = await cosyvoice2_service.save_voice(audio, voice_name, voice_text, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "code": 200,
        "message": "语音保存成功",
        "data": {
            "voice_id": voice_result["voice_id"],
            "voice_wav_url": voice_result["voice_url"],
            "duration": voice_result["duration"]
        }
    }


@router.get("/voices", summary="获取所有声音")
async def list_voices(skip: int = 0, limit: int = 100):
    """获取所有已保存的声音"""
    voices = cosyvoice2_service.get_all_voices(skip, limit)
    # voices = db.list_voices(skip, limit)

    # 手动将每个 Voice 对象转换为字典
    voices_data = []
    for v in voices:
        voice_dict = {
            "voice_id": v.voice_id,
            "voice_name": v.voice_name,
            "voice_text": v.voice_text,
            "voice_url": v.voice_url,
            "duration": v.duration,
            "sample_rate": getattr(v, 'sample_rate', None),
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "user_id": v.user_id
        }
        voices_data.append(voice_dict)

    return {
        "code": 200,
        "message": "语音保存成功",
        "data": {

            "voices": voices_data
        }

    }


@router.post("/generate")
async def generate_voice(request: GenerateRequest):
    text= request.text,
    if isinstance(text, tuple):
        text = text[0]  # 提取第一个元素
    # print(text)
    voice_id =request.voice_id

    logger.info(f"Generating voice for voice_id={voice_id} with text='{text}'")

    audio_url = cosyvoice2_service.generate(
        text,
        voice_id
    )

    return {
        "code": 200,
        "message": "生成成功",
        "audio_url": audio_url
    }

#
#
# router.get("/voices/{voice_id}", summary="获取声音详情")
# async def get_voice(voice_id: str):
#     """获取单个声音的详细信息"""
#     voice = VoiceDB.get_voice(voice_id)
#     if not voice:
#         raise HTTPException(status_code=404, detail="声音不存在")
#
#     # 获取这个声音生成的所有音频
#     generated = GeneratedAudioDB.list_by_voice(voice_id)
#
#     return {
#         "voice": voice.to_dict(),
#         "generated_count": len(generated),
#         "recent_generations": [g.to_dict() for g in generated[:5]]
#     }
#
#
# router.delete("/voices/{voice_id}", summary="删除声音")
# async def delete_voice(voice_id: str):
#     """删除声音（同时删除音频文件）"""
#     success = VoiceDB.delete_voice(voice_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="声音不存在")
#
#     return {"success": True, "message": "声音已删除"}
