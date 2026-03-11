import uuid
import logging
from pathlib import Path

import os
import sys
import torch
import soundfile as sf

from app.core.config import Settings
from app.repositories import voice_repo
from app.repositories.voice_repo import VoiceRepository

settings = Settings()
cosyvice_path = settings.COSYVOICE_PATH
if cosyvice_path not in sys.path:
    sys.path.insert(0, str(cosyvice_path))
    print(f"✅ 添加路径: {cosyvice_path}")
# 导入 CosyVoice
try:
    from CosyVoice.cosyvoice.cli.cosyvoice import CosyVoice2
    from CosyVoice.cosyvoice.utils.file_utils import load_wav

    print("✅ CosyVoice 导入成功！")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保 CosyVoice 路径正确")
    sys.exit(1)

logger = logging.getLogger(__name__)
voice_repo = VoiceRepository()


class CosyVoice2Service:

    def __init__(self, model_path):
        self.model = CosyVoice2(
            model_path,
            load_jit=False,
            load_trt=False,
            load_vllm=False,
            fp16=False  # 必须是 False
        )

    async def save_voice(self, audio, voice_name, voice_text, user_id):
        suffix = Path(audio.filename).suffix
        logger.info(
            f"接收声音: voice_name={voice_name}, voice_text={voice_text}, filename={audio.filename}, suffix={suffix}")

        if not suffix or suffix not in [".wav", ".mp3"]:
            logger.warning(f"文件格式不支持，自动转为wav：{audio.filename}")
            raise ValueError("不支持的文件格式，请上传wav或mp3格式的音频")
        voice_id = "voice_" + uuid.uuid4().hex[:8]

        # voice_path = os.path.join(settings.COSYVOICE_SAMPLE_DIR, f"voice_id.wav")
        voice_path = settings.COSYVOICE2_SAMPLE_DIR / f"{voice_id}{suffix}"
        voice_url = f"/static/cosyvoice/cosyvoice2_sample/{voice_id}{suffix}"
        voice_path.parent.mkdir(parents=True, exist_ok=True)
        with open(voice_path, "wb") as f:
            f.write(await audio.read())

        # 获取音频信息
        data, sr = sf.read(voice_path)
        duration = round(len(data) / sr, 2)
        logger.info(
            f"保存声音: voice_id={voice_id}, voice_name={voice_name}, voice_text={voice_text}, wav_path={voice_path}, duration={duration}, user_id={user_id}")

        voice_repo.save_voice(voice_id, voice_name, voice_text, voice_url, duration, user_id)

        return {
            "voice_id": voice_id,
            "voice_url": voice_url,
            "duration": duration
        }

    def get_all_voices(self, skip, limit):

        return voice_repo.list_voices(skip, limit)

    def generate(self, text, voice_id):

        # 检查 CUDA
        if torch.cuda.is_available():
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
            print(f"   显存: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.1f} GB")

        print("\n🔧 强制转换子模块精度到 Float32...")
        try:
            # CosyVoice2Model 有三个核心子模块
            for name, submodule in [('llm', self.model.model.llm),
                                    ('flow', self.model.model.flow),
                                    ('hift', self.model.model.hift)]:
                if hasattr(submodule, 'to'):
                    submodule.to(torch.float32)
                    print(f"   ✅ {name} → Float32")
                else:
                    print(f"   ⚠️ {name} 无法转换")
            print("✅ 精度转换完成")
        except Exception as e:
            print(f"⚠️ 精度转换警告: {e}（可尝试继续运行）")

        voice = voice_repo.get_voice_by_id(voice_id)
        prompt_text = voice.voice_text
        prompt_wav = "E:/Code/Python/AIChat" + voice.voice_url
        # text=str(text)
        output_file_name = voice_id + uuid.uuid4().hex[:16] + ".wav"
        output_file = settings.COSYVOICE2_OUTPUT_DIR / output_file_name
        # logger.info(f"生成语音: text={text}, voice_id={voice_id}, prompt_text={prompt_text}, prompt_wav={prompt_wav}, output_file={output_file}")

        try:
            # ✅ 正确：传入音频文件路径，而不是音频数据
            for i, output in enumerate(self.model.inference_zero_shot(
                    text,  # 要生成的文本
                    prompt_text,  # 参考音频的文本内容
                    prompt_wav,  # 直接传入音频文件路径，不要用 load_wav！
                    text_frontend=False,
            )):
                # output_file = "cloned_voice.wav"

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

                print(f"\n✅ 克隆成功！")
                print(f"   - 输出文件: {output_file}")
                print(f"   - 音频时长: {duration:.2f}秒")
                print(f"   - 采样率: {sr}Hz")
                print(f"   - 文件大小: {os.path.getsize(output_file) / 1024:.1f}KB")

                # 可选：播放提示
                print(f"\n💡 可以用播放器打开: {os.path.abspath(output_file)}")

                audio_url = f"/static/cosyvoice/cosyvoice2_output/{output_file_name}"

                return audio_url


        except Exception as e:
            print(f"❌ 克隆失败: {e}")
            import traceback

            traceback.print_exc()


cosyvoice2_service = CosyVoice2Service(model_path=settings.COSYVOICE2_MODEL_DIR)
