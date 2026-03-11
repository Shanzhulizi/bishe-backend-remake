# # app/api/v1/xtts.py
#
# import uuid
#
# from fastapi import APIRouter, Form
#
# from app.core.config import settings
# from app.services.xtts_service import xtts_service
#
# import shutil
# import uuid
# from pathlib import Path
# from typing import List, Dict
#
# import edge_tts
# from fastapi import APIRouter, UploadFile, File, Form
# from fastapi import Depends
#
# from app.api.deps import get_current_user
# from app.core.config import settings
# from app.core.constants import ResponseCode
# from app.core.logging import get_logger
# from app.schemas.common import ResponseModel
# from app.schemas.voice import ASRResponse, TTSResponse, TTSRequest
# from app.services.ars_service import ASRService
# from app.services.tts_service import TTSService
# from app.services.xtts_service import create_voice, generate_speech
#
# router = APIRouter()
# logger= get_logger(__name__)
#
# @router.post("/tts")
# async def generate_voice(
#         text: str = Form(...),
#         voice_id: str = Form(...)
# ):
#     try:
#         print(f"收到TTS请求: voice_id={voice_id}, text={text[:20]}...")
#
#         # 查找声音文件
#         sample_path = settings.VOICE_MODELS_DIR / f"{voice_id}.wav"
#         if not sample_path.exists():
#             return {
#                 "code": 404,
#                 "msg": f"声音不存在: {voice_id}",
#                 "data": None
#             }
#
#         # 确保输出目录存在
#         output_dir = settings.AUDIO_FILES_DIR
#         output_dir.mkdir(parents=True, exist_ok=True)
#
#         output_filename = f"speech_{uuid.uuid4().hex}.wav"
#         output_path = output_dir / output_filename
#
#         # ✅ 改为 tts_to_file
#         xtts_service.tts_to_file(
#             text=text,
#             speaker_wav=str(sample_path),
#             output_path=str(output_path),
#             language="zh"
#         )
#
#         return {
#             "code": 200,
#             "msg": "生成成功",
#             "data": {
#                 "audio_url": f"/static/audio_files/{output_filename}"
#             }
#         }
#     except Exception as e:
#         print(f"TTS错误: {e}")
#         import traceback
#         traceback.print_exc()
#         return {
#             "code": 500,
#             "msg": str(e),
#             "data": None
#         }
#
#
#
#
#
#
#
#
#
# # 临时上传目录
# TEMP_DIR = Path("static/temp_uploads")
# TEMP_DIR.mkdir(parents=True, exist_ok=True)
#
#
# @router.post("/create")
# async def create_voice_api(
#         name: str = Form(...),
#         audio: UploadFile = File(...)
# ):
#     """
#     创建声音 - 上传音频，返回声音ID和预览URL
#     """
#     temp_path = None
#
#     try:
#         # 保存上传的音频
#         ext = Path(audio.filename).suffix
#         temp_filename = f"temp_{uuid.uuid4().hex}{ext}"
#         temp_path = TEMP_DIR / temp_filename
#
#         with open(temp_path, "wb") as f:
#             shutil.copyfileobj(audio.file, f)
#
#         # 创建声音
#         result = create_voice(str(temp_path))
#
#         return {
#             "code": 200,
#             "msg": "声音创建成功",
#             "data": result
#         }
#
#     except Exception as e:
#         return {
#             "code": 500,
#             "msg": str(e),
#             "data": None
#         }
#     finally:
#         # 清理临时文件
#         if temp_path and temp_path.exists():
#             temp_path.unlink()
#
#
# @router.post("/speak")
# async def speak(
#         text: str = Form(...),
#         voice_id: str = Form(...)
# ):
#     """
#     用已创建的声音生成语音
#     """
#     try:
#         audio_url = generate_speech(text, voice_id)
#         logger.info(f"生成语音成功，URL: {audio_url}")
#         return {
#             "code": 200,
#             "msg": "生成成功",
#             "data": {
#                 "audio_url": audio_url
#             }
#         }
#     except FileNotFoundError:
#         return {
#             "code": 404,
#             "msg": "声音不存在",
#             "data": None
#         }
#     except Exception as e:
#         return {
#             "code": 500,
#             "msg": str(e),
#             "data": None
#         }
