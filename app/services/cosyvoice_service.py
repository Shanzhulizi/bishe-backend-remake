import hashlib
import logging
import os
import sys
import uuid
from pathlib import Path

import soundfile as sf
import torch

from app.core.config import Settings
from app.repositories import voice_repo
from app.repositories.voice_repo import VoiceRepository

logger = logging.getLogger(__name__)
settings = Settings()
cosyvice_path = settings.COSYVOICE_PATH
if cosyvice_path not in sys.path:
    sys.path.insert(0, str(cosyvice_path))
    logger.info(f"✅ 添加路径: {cosyvice_path}")
# 导入 CosyVoice
try:
    from CosyVoice.cosyvoice.cli.cosyvoice import CosyVoice
    from CosyVoice.cosyvoice.utils.file_utils import load_wav

    logger.info("✅ CosyVoice 导入成功！")
except ImportError as e:
    logger.info(f"❌ 导入失败: {e}")
    logger.info("请确保 CosyVoice 路径正确")
    sys.exit(1)

# 检查 CUDA
if torch.cuda.is_available():
    logger.info(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"   显存: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.1f} GB")

logger = logging.getLogger(__name__)
voice_repo = VoiceRepository()


class CosyVoiceService:

    def __init__(self, model_path):
        self.model = CosyVoice(model_path)

    def generate(self, text, voice_id):
        # 生成缓存键
        cache_key = hashlib.md5(f"{text}_{voice_id}".encode()).hexdigest()
        cache_file = settings.COSYVOICE_OUTPUT_DIR / f"{cache_key}.wav"

        # 检查缓存
        if cache_file.exists():
            logger.info(f"✅ 使用缓存的音频: {cache_file}")
            audio_url = settings.LOCAL_HOST + f"/static/cosyvoice/cosyvoice_output/{cache_key}.wav"
            logger.info(f"返回缓存音频 URL: {audio_url}")
            return audio_url

        voice = voice_repo.get_voice_by_id(voice_id)
        prompt_text = voice.voice_text
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        voice_path = '/static' + voice.voice_url.split('/static')[1]
        prompt_wav = str(BASE_DIR) + voice_path
        # prompt_wav = str(BASE_DIR )+ voice.voice_url
        logger.info(f"路径信息: BASE_DIR={BASE_DIR} ,prompt_wav={prompt_wav}")

        # text=str(text)
        # output_file_name = voice_id + uuid.uuid4().hex[:16] + ".wav"
        output_file = settings.COSYVOICE_OUTPUT_DIR / f"{cache_key}.wav"
        # logger.info(f"生成语音: text={text}, voice_id={voice_id}, prompt_text={prompt_text}, prompt_wav={prompt_wav}, output_file={output_file}")

        try:
            # ✅ 正确：传入音频文件路径，而不是音频数据
            for i, output in enumerate(self.model.inference_zero_shot(
                    text,  # 要生成的文本
                    prompt_text,  # 参考音频的文本内容
                    prompt_wav  # 直接传入音频文件路径，不要用 load_wav！
            )):

                # 改为：
                tts_speech = output['tts_speech']
                if torch.is_tensor(tts_speech):
                    tts_speech = tts_speech.cpu().numpy()
                if len(tts_speech.shape) > 1:
                    tts_speech = tts_speech.squeeze()
                sf.write(output_file, tts_speech, 22050)

                # 获取音频信息
                audio_out, sr = sf.read(output_file)
                duration = len(audio_out) / sr

                logger.info(
                    f"✅ 克隆成功！输出文件: {output_file} (时长: {duration:.2f}s, 采样率: {sr}Hz, 大小: {os.path.getsize(output_file) / 1024:.1f}KB)")

                # 可选：播放提示
                logger.info(f"\n💡 可以用播放器打开: {os.path.abspath(output_file)}")

                audio_url = settings.LOCAL_HOST + f"/static/cosyvoice/cosyvoice_output/{cache_key}.wav"

                return audio_url


        except Exception as e:
            logger.info(f"❌ 克隆失败: {e}")
            import traceback

            traceback.print_exc()


# cosyvoice_service = CosyVoiceService(model_path=settings.COSYVOICE_MODEL_DIR)
