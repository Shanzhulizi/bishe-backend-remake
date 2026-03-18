import hashlib
import logging
import os
import sys
import time
from pathlib import Path

import soundfile as sf
import torch

from app.core.config import Settings
from app.core.logging import get_logger
from app.repositories import voice_repo
from app.repositories.voice_repo import VoiceRepository


logger = get_logger(__name__)

settings = Settings()
cosyvice_path = settings.COSYVOICE_PATH
if cosyvice_path not in sys.path:
    sys.path.insert(0, str(cosyvice_path))
    logger.info(f"✅ 添加路径: {cosyvice_path}")
# 导入 CosyVoice
try:
    from CosyVoice.cosyvoice.cli.cosyvoice import CosyVoice2
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

voice_repo = VoiceRepository()


class CosyVoice2Service:

    def __init__(self, model_path):
        self.model = CosyVoice2(
            model_path,
            load_jit=False,
            load_trt=False,
            load_vllm=False,
            fp16=True  # 必须是 False
        )

        # 初始化后立即修复特征提取器
        self._fix_feat_extractor()

    def _fix_feat_extractor(self):
        """初始化时修复特征提取器"""
        try:
            import torch

            # 获取特征提取器
            feat_extractor = self.model.frontend.feat_extractor

            # 正确的配置
            n_fft = 1920
            win_length = 1920
            hop_length = 480

            # 创建正确的窗函数
            correct_window = torch.hann_window(win_length)

            # 替换窗函数
            if hasattr(feat_extractor, 'window'):
                feat_extractor.window = correct_window
                print(f"✅ 窗函数已修复: 大小={len(correct_window)}")

            # 确保参数一致
            if hasattr(feat_extractor, 'n_fft'):
                feat_extractor.n_fft = n_fft
            if hasattr(feat_extractor, 'win_length'):
                feat_extractor.win_length = win_length
            if hasattr(feat_extractor, 'hop_length'):
                feat_extractor.hop_length = hop_length
            logger.info("特征提取器初始化修复完成")

        except Exception as e:
            logger.info(f"⚠️ 特征提取器修复失败: {e}")

    def generate(self, text, voice_id):

        t0 = time.perf_counter()

        # 生成缓存键
        cache_key = hashlib.md5(f"{text}_{voice_id}".encode()).hexdigest()
        cache_file = settings.COSYVOICE2_OUTPUT_DIR / f"{cache_key}.wav"

        # 检查缓存
        if cache_file.exists():
            logger.info(f"✅ 使用缓存的音频: {cache_file}")
            audio_url = settings.LOCAL_HOST + f"/static/cosyvoice/cosyvoice2_output/{cache_key}.wav"
            logger.info(f"返回缓存音频 URL: {audio_url}")
            return audio_url

        t1 = time.perf_counter()
        logger.info("\n🔧 强制转换子模块精度到 Float32...")
        # try:
        #     # CosyVoice2Model 有三个核心子模块
        #     for name, submodule in [('llm', self.model.model.llm),
        #                             ('flow', self.model.model.flow),
        #                             ('hift', self.model.model.hift)]:
        #         if hasattr(submodule, 'to'):
        #             submodule.to(torch.float32)
        #             logger.info(f"   ✅ {name} → Float32")
        #         else:
        #             logger.info(f"   ⚠️ {name} 无法转换")
        #     logger.info("✅ 精度转换完成")
        # except Exception as e:
        #     logger.info(f"⚠️ 精度转换警告: {e}（可尝试继续运行）")

        voice = voice_repo.get_voice_by_id(voice_id)
        prompt_text = voice.voice_text
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        voice_path = '/static' + voice.voice_url.split('/static')[1]
        prompt_wav = str(BASE_DIR) + voice_path
        logger.info(f"路径信息: BASE_DIR={BASE_DIR} ,prompt_wav={prompt_wav}")
        # text=str(text)
        # output_file_name = f"{cache_key}.wav"
        output_file = settings.COSYVOICE2_OUTPUT_DIR / f"{cache_key}.wav"
        # logger.info(f"生成语音: text={text}, voice_id={voice_id}, prompt_text={prompt_text}, prompt_wav={prompt_wav}, output_file={output_file}")

        t2 = time.perf_counter()

        try:
            # ✅ 正确：传入音频文件路径，而不是音频数据
            for i, output in enumerate(self.model.inference_zero_shot(
                    text,  # 要生成的文本
                    prompt_text,  # 参考音频的文本内容
                    prompt_wav,  # 直接传入音频文件路径，不要用 load_wav！
                    text_frontend=False,
            )):
                t3 = time.perf_counter()
                # 改为：
                tts_speech = output['tts_speech']
                if torch.is_tensor(tts_speech):
                    tts_speech = tts_speech.cpu().numpy()
                if len(tts_speech.shape) > 1:
                    tts_speech = tts_speech.squeeze()
                sf.write(output_file, tts_speech, 22050)

                t4 = time.perf_counter()

                # 获取音频信息
                audio_out, sr = sf.read(output_file)
                duration = len(audio_out) / sr

                logger.info(f"\n✅ 克隆成功！输出文件: {output_file} (时长: {duration:.2f}s, 采样率: {sr}Hz, 大小: {os.path.getsize(output_file) / 1024:.1f}KB)" )
                # 可选：播放提示
                logger.info(f"\n💡 可以用播放器打开: {os.path.abspath(output_file)}")

                audio_url = settings.LOCAL_HOST + f"/static/cosyvoice/cosyvoice2_output/{cache_key}.wav"
                logger.info(
                    f"⏱️ CosyVoice2耗时统计:\n"
                    f"   参数准备: {(t2 - t1) * 1000:.1f} ms\n"
                    f"   模型推理: {(t3 - t2) * 1000:.1f} ms\n"
                    f"   音频写入: {(t4 - t3) * 1000:.1f} ms\n"
                    f"   总耗时: {(t4 - t0):.2f} s"
                )
                return audio_url


        except Exception as e:
            logger.info(f"❌ 克隆失败: {e}")
            import traceback

            traceback.print_exc()


cosyvoice2_service = CosyVoice2Service(model_path=settings.COSYVOICE2_MODEL_DIR)
