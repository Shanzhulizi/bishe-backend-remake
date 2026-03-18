# import hashlib
# import logging
# import sys
# from pathlib import Path
#
# import numpy as np
# import torch
#
# from app.core.config import Settings
# from app.repositories import voice_repo
# from app.repositories.voice_repo import VoiceRepository
#

# logger = get_logger(__name__)
# from app.core.logging import get_logger
#
# logger = get_logger(__name__)

# settings = Settings()
# cosyvice_path = settings.COSYVOICE_PATH
# if cosyvice_path not in sys.path:
#     sys.path.insert(0, str(cosyvice_path))
#     logger.info(f"✅ 添加路径: {cosyvice_path}")
# # 导入 CosyVoice
# try:
#     from CosyVoice.cosyvoice.cli.cosyvoice import CosyVoice2
#     from CosyVoice.cosyvoice.utils.file_utils import load_wav
#
#     logger.info("✅ CosyVoice 导入成功！")
# except ImportError as e:
#     logger.info(f"❌ 导入失败: {e}")
#     logger.info("请确保 CosyVoice 路径正确")
#     sys.exit(1)
# # 检查 CUDA
# if torch.cuda.is_available():
#     logger.info(f"✅ GPU: {torch.cuda.get_device_name(0)}")
#     logger.info(f"   显存: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.1f} GB")
#
# voice_repo = VoiceRepository()
#
#
# class CosyVoice2StreamService:
#
#     def __init__(self, model_path):
#         self.model = CosyVoice2(
#             model_path,
#             load_jit=False,
#             load_trt=False,
#             load_vllm=False,
#             fp16=True  # 必须是 False
#         )
#
#         # 将模型子模块移动到 GPU
#         for name, submodule in [('llm', self.model.model.llm),
#                                 ('flow', self.model.model.flow),
#                                 ('hift', self.model.model.hift)]:
#             if hasattr(submodule, 'to'):
#                 submodule.to(torch.device("cuda"))
#         # 初始化后立即修复特征提取器
#         self._fix_feat_extractor()
#
#
#     def _fix_feat_extractor(self):
#         """初始化时修复特征提取器"""
#         try:
#             import torch
#
#             # 获取特征提取器
#             feat_extractor = self.model.frontend.feat_extractor
#
#             # 正确的配置
#             n_fft = 1920
#             win_length = 1920
#             hop_length = 480
#
#             # 创建正确的窗函数
#             correct_window = torch.hann_window(win_length)
#
#             # 替换窗函数
#             if hasattr(feat_extractor, 'window'):
#                 feat_extractor.window = correct_window
#                 print(f"✅ 窗函数已修复: 大小={len(correct_window)}")
#
#             # 确保参数一致
#             if hasattr(feat_extractor, 'n_fft'):
#                 feat_extractor.n_fft = n_fft
#             if hasattr(feat_extractor, 'win_length'):
#                 feat_extractor.win_length = win_length
#             if hasattr(feat_extractor, 'hop_length'):
#                 feat_extractor.hop_length = hop_length
#             logger.info("特征提取器初始化修复完成")
#
#         except Exception as e:
#             logger.info(f"⚠️ 特征提取器修复失败: {e}")
#
#
#     def generate_audio_stream(self, text, voice_id):
#         # 生成缓存键
#         cache_key = hashlib.md5(f"{text}_{voice_id}".encode()).hexdigest()
#         cache_file = settings.COSYVOICE2_OUTPUT_DIR / f"{cache_key}.wav"
#
#         # 检查缓存
#         if cache_file.exists():
#             logger.info(f"✅ 使用缓存音频: {cache_file}")
#
#             def cached_file_gen():
#                 with open(cache_file, "rb") as f:
#                     while chunk := f.read(8192):
#                         yield chunk
#
#             return cached_file_gen()
#
#
#         # 获取声音样本
#         voice = voice_repo.get_voice_by_id(voice_id)
#         prompt_text = voice.voice_text
#         BASE_DIR = Path(__file__).resolve().parent.parent.parent
#         voice_path = '/static' + voice.voice_url.split('/static')[1]
#         prompt_wav = str(BASE_DIR) + voice_path
#
#         sample_rate = 22050
#         channels = 1
#         sample_width = 2  # 16-bit
#
#         # 先发送WAV header（数据大小先设为0，后面不更新也没关系，浏览器会忽略）
#         header = self._create_wav_header(sample_rate, channels, sample_width, 0)
#
#         def generate():
#             # 发送WAV header
#             yield header
#
#             # 生成并发送音频块
#             for output in cosyvoice2_stream_service.model.inference_zero_shot(
#                     text,
#                     prompt_text,
#                     prompt_wav,
#                     text_frontend=False,
#                     stream=True
#             ):
#                 tts_speech = output['tts_speech']
#                 if hasattr(tts_speech, "cpu"):
#                     tts_speech = tts_speech.cpu().numpy()
#                 if len(tts_speech.shape) > 1:
#                     tts_speech = tts_speech.squeeze()
#
#                 # 转换为PCM16字节
#                 pcm16 = (tts_speech * 32767).astype(np.int16)
#                 yield pcm16.tobytes()
#
#
#
#             # 异步保存缓存（不阻塞返回）
#             import threading
#             def save_cache():
#                 all_chunks = []
#                 # 这里需要重新生成或从某处获取所有chunks
#                 # 简化：可以保存最后一个或使用其他机制
#                 pass
#
#             threading.Thread(target=save_cache).start()
#
#         return generate()
#
#
#     def _create_wav_header(self, sample_rate, channels, sample_width, data_size):
#         """创建WAV文件头"""
#         import struct
#
#         byte_rate = sample_rate * channels * sample_width
#         block_align = channels * sample_width
#
#         header = struct.pack(
#             '<4sI4s4sIHHIIHH4sI',
#             b'RIFF',
#             36 + data_size,
#             b'WAVE',
#             b'fmt ',
#             16,
#             1,
#             channels,
#             sample_rate,
#             byte_rate,
#             block_align,
#             sample_width * 8,
#             b'data',
#             data_size
#         )
#         return header
#
#
# cosyvoice2_stream_service = CosyVoice2StreamService(model_path=settings.COSYVOICE2_MODEL_DIR)
