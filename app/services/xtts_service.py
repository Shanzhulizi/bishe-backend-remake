#
# import logging
# import os
# import uuid
#
# from TTS.api import TTS
#
# from app.core.config import settings
#
# logger = logging.getLogger(__name__)
#
#
# class XTTSService:
#     """XTTS 服务 - 完全模仿测试代码"""
#
#     _instance = None
#     _model = None
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#         return cls._instance
#
#     def __init__(self):
#         if self._model is None:
#             # 设置环境变量
#             os.environ['TTS_HOME'] = str(settings.XTTS_MODEL_DIR)
#             os.environ['TORCH_HOME'] = str(settings.XTTS_MODEL_DIR.parent)
#             self._load_model()
#
#     def _load_model(self):
#         """加载 XTTS 模型 - 和测试代码完全一样"""
#         try:
#             logger.info("正在加载 XTTS 模型...")
#             # 直接加载，不加多余参数
#             self._model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
#             logger.info("✅ XTTS 模型加载成功")
#         except Exception as e:
#             logger.error(f"XTTS 模型加载失败: {e}")
#             raise e
#
#     def tts_to_file(self, text, speaker_wav, output_path, language="zh"):
#         """
#         直接调用模型的 tts_to_file - 和测试代码完全一样
#         """
#         try:
#
#             logger.info(f"生成语音: {text[:20]}...")
#             logger.info(f"使用 speaker_wav: {speaker_wav}")
#             # 确保输出目录存在
#             os.makedirs(os.path.dirname(output_path), exist_ok=True)
#
#             # 直接调用，不加任何包装
#             self._model.tts_to_file(
#                 text=text,
#                 file_path=output_path,
#                 speaker_wav=speaker_wav,
#                 language=language,
#                 speed=1.0,  # 可以调整这个参数来控制语速
#                 temperature=0.9  # 可以调整这个参数来控制声音的多样性
#             )
#
#             logger.info(f"语音已生成: {output_path}")
#             return output_path
#
#         except Exception as e:
#             logger.error(f"生成语音失败: {e}")
#             raise e
#
#
#
# def create_voice(sample_path: str) -> dict:
#     """
#     创建声音模型 - 只保存文件，生成预览
#     """
#     voice_id = str(uuid.uuid4())
#     print(f"创建声音: {voice_id}")
#
#     # 1. 复制样本到永久存储
#     import shutil
#     audio_path = settings.VOICE_MODELS_DIR / f"{voice_id}.wav"
#     audio_path.parent.mkdir(parents=True, exist_ok=True)
#     shutil.copy2(sample_path, audio_path)
#
#     # 2. 生成预览音频 - 直接用 tts_to_file
#     preview_path = settings.VOICE_MODELS_DIR / f"{voice_id}_preview.wav"
#     xtts_service.tts_to_file(
#         text="你好，我是你的AI助手，很高兴认识你。",
#         speaker_wav=str(audio_path),
#         output_path=str(preview_path),
#         language="zh"
#     )
#     logger.info(f"预览音频已生成: {preview_path}")
#
#     return {
#         "voice_id": voice_id,
#         "preview_url": f"/static/voice_models/{voice_id}_preview.wav"
#     }
#
#
# def generate_speech(text: str, voice_id: str) -> str:
#     """
#     用已创建的声音生成语音 - 直接用 tts_to_file
#     """
#     print(f"生成语音: voice_id={voice_id}, text={text[:20]}...")
#
#     # 查找原始音频文件
#     audio_path = settings.VOICE_MODELS_DIR / f"{voice_id}.wav"
#     if not audio_path.exists():
#         raise FileNotFoundError(f"Voice {voice_id} not found")
#
#     # 生成输出文件
#     output_filename = f"speech_{uuid.uuid4().hex}.wav"
#     output_path = settings.AUDIO_FILES_DIR / output_filename
#     output_path.parent.mkdir(parents=True, exist_ok=True)
#
#     # 直接调用 tts_to_file - 和测试代码一样
#     xtts_service.tts_to_file(
#         text=text,
#         speaker_wav=str(audio_path),
#         output_path=str(output_path),
#         language="zh"
#     )
#
#     return f"/static/audio_files/{output_filename}"
# # 全局实例
# xtts_service = XTTSService()