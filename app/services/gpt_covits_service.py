import asyncio
import hashlib
import os
import sys
from pathlib import Path

import soundfile as sf

from app.core.config import Settings
from app.core.logging import get_logger
from app.repositories.voice_repo import VoiceRepository

# 设置项目根目录
project_root = r"E:\Code\Python\AIChat\GPT-SoVITS-main"

# 先添加所有必要的路径
paths_to_add = [
    project_root,
    os.path.join(project_root, "GPT_SoVITS"),
    os.path.join(project_root, "GPT_SoVITS", "text"),
    os.path.join(project_root, "GPT_SoVITS", "feature_extractor"),
    os.path.join(project_root, "tools"),
    os.path.join(project_root, "tools", "i18n"),
]

for path in paths_to_add:
    if path not in sys.path and os.path.exists(path):
        sys.path.insert(0, str(path))

# 导入 inference_webui 模块本身，而不是单独导入变量
import GPT_SoVITS.inference_webui as inference_webui

# 从模块中获取需要的函数和变量
get_tts_wav = inference_webui.get_tts_wav
change_gpt_weights = inference_webui.change_gpt_weights
change_sovits_weights = inference_webui.change_sovits_weights
dict_language = inference_webui.dict_language
is_half = inference_webui.is_half
device = inference_webui.device

# 注意：hps 在模块加载时还没有定义，需要在调用 change_sovits_weights 后才能获取

from tools.i18n.i18n import I18nAuto

settings = Settings()
logger = get_logger(__name__)


class GptCovitsService:
    # 类变量，所有实例共享
    _model_initialized = False
    _gpt_path = None
    _sovits_path = None
    _i18n = None
    _get_tts_wav = None
    _change_gpt_weights = None
    _change_sovits_weights = None
    _dict_language = None
    _hps = None
    _is_half = None
    _device = None
    _inference_webui = None  # 保存模块引用

    def __init__(self, db):
        self.db = db
        self.voice_repo = VoiceRepository(db)
        self._initialize_model()

    @classmethod
    def _initialize_model(cls):
        """类方法：初始化模型（只执行一次）"""
        if cls._model_initialized:
            logger.info("✅ 模型已经初始化过，跳过")
            return

        try:
            logger.info("🚀 正在初始化 GPT-SoVITS 模型...")

            # 保存模块引用
            cls._inference_webui = inference_webui

            # 硬编码模型路径
            gpt_path = r"E:\Code\Python\AIChat\GPT-SoVITS-main\GPT_SoVITS\pretrained_models\s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt"
            sovits_path = r"E:\Code\Python\AIChat\GPT-SoVITS-main\GPT_SoVITS\pretrained_models\s2G488k.pth"

            # 检查文件是否存在
            if not os.path.exists(gpt_path):
                logger.error(f"❌ GPT 权重文件不存在: {gpt_path}")
                raise FileNotFoundError(f"找不到 GPT 权重文件: {gpt_path}")

            if not os.path.exists(sovits_path):
                logger.error(f"❌ SoVITS 权重文件不存在: {sovits_path}")
                raise FileNotFoundError(f"找不到 SoVITS 权重文件: {sovits_path}")

            # 设置环境变量
            os.environ['gpt_path'] = gpt_path
            os.environ['sovits_path'] = sovits_path

            # 保存函数为类变量
            cls._get_tts_wav = get_tts_wav
            cls._change_gpt_weights = change_gpt_weights
            cls._change_sovits_weights = change_sovits_weights
            cls._dict_language = dict_language
            cls._is_half = is_half
            cls._device = device
            cls._i18n = I18nAuto()

            # 加载 GPT 权重
            logger.info("🔧 加载 GPT 模型权重...")
            change_gpt_weights(gpt_path)

            # 加载 SoVITS 权重 - 传入有效的语言参数
            logger.info("🔧 加载 SoVITS 模型权重...")

            # 获取有效的语言选项
            language_options = list(dict_language.keys())
            default_language = "中文" if "中文" in language_options else language_options[0]

            # 调用生成器并获取所有输出
            results = []
            try:
                for result in change_sovits_weights(sovits_path, default_language, default_language):
                    results.append(result)
                    # 可以根据需要处理每个结果
                    if len(results) == 1:
                        logger.info("✅ SoVITS 权重加载第一步完成")
                    elif len(results) >= 9:  # change_sovits_weights 通常会 yield 多次
                        logger.info(f"✅ SoVITS 权重加载完成，收到 {len(results)} 个结果")
            except Exception as e:
                logger.error(f"❌ SoVITS 权重加载失败: {e}")
                # 即使出错，也可能已经设置了 hps
                pass

            # 尝试获取 hps
            if hasattr(inference_webui, 'hps'):
                cls._hps = inference_webui.hps
                logger.info("✅ 成功获取 hps")
            elif hasattr(inference_webui, '__dict__') and 'hps' in inference_webui.__dict__:
                cls._hps = inference_webui.__dict__['hps']
                logger.info("✅ 通过 __dict__ 成功获取 hps")
            else:
                logger.error("❌ 无法获取 hps，尝试手动创建")
                # 如果还是无法获取，可能需要手动创建 hps
                # 这里可以根据需要添加手动创建 hps 的逻辑
                raise AttributeError("hps not found in inference_webui module")

            cls._model_initialized = True
            logger.info("✅ GPT-SoVITS 模型初始化完成！")

        except Exception as e:
            logger.error(f"❌ 模型初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def generate_voice(self, text: str, voice_id: str) -> str:
        # 确保模型已初始化
        if not self.__class__._model_initialized:
            self._initialize_model()

        # 加缓存
        cache_key = hashlib.md5(f"{text}_{voice_id}".encode()).hexdigest()
        cache_file = settings.GPT_SoVITS_OUTPUT_DIR / f"{cache_key}.wav"

        # 检查缓存
        if cache_file.exists():
            logger.info(f"✅ 使用缓存的音频: {cache_file}")
            audio_url = settings.LOCAL_HOST + f"/static/voice/gpt_sovits_output/{cache_key}.wav"
            return audio_url

        # 获取参考音频
        voice =await self.voice_repo.get_voice_by_id(voice_id)
        prompt_text = voice.voice_text
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        voice_path = '/static' + voice.voice_url.split('/static')[1]
        prompt_wav = str(BASE_DIR) + voice_path
        logger.info(f"路径信息: BASE_DIR={BASE_DIR}, prompt_wav={prompt_wav}")

        # 执行克隆
        # output_path = rf"E:\Code\Python\AIChat\static\gpt-covits\output\{cache_key}.wav"
        output_path = settings.GPT_SoVITS_OUTPUT_DIR / f"{cache_key}.wav"

        # result = self._clone_voice(
        #     prompt_wav,
        #     prompt_text,
        #     text,
        #     str(output_path)
        # )

        # 执行克隆（在线程池中运行，因为 TTS 是 CPU 密集型）
        output_path = settings.GPT_SoVITS_OUTPUT_DIR / f"{cache_key}.wav"

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._clone_voice,
            prompt_wav,
            prompt_text,
            text,
            str(output_path)
        )
        if result:
            audio_url = settings.LOCAL_HOST + f"/static/voice/gpt_sovits_output/{cache_key}.wav"
            return audio_url
        else:
            raise Exception("语音生成失败")

    def _clone_voice(self, reference_audio, reference_text, target_text, output_path="output.wav"):
        """
        声音克隆函数
        """
        # 检查文件是否存在
        if not os.path.exists(reference_audio):
            logger.error(f"❌ 参考音频不存在: {reference_audio}")
            return None

        # 使用类变量
        get_tts_wav = self.__class__._get_tts_wav
        dict_language = self.__class__._dict_language

        # 确保 hps 在全局命名空间中可用
        # get_tts_wav 函数内部会访问 hps，我们需要确保它在模块中
        if self.__class__._hps:
            # 将 hps 设置到 inference_webui 模块
            self.__class__._inference_webui.hps = self.__class__._hps

        # 使用显示文本作为语言键
        prompt_language = "中文"
        text_language = "中文"

        logger.info(f"使用语言: {prompt_language} -> {dict_language.get(prompt_language, 'unknown')}")

        # 设置参数
        tts_params = {
            "ref_wav_path": reference_audio,
            "prompt_text": reference_text,
            "prompt_language": prompt_language,
            "text": target_text,
            "text_language": text_language,
            "how_to_cut": "凑四句一切",
            "top_k": 5,
            "top_p": 0.95,
            "temperature": 0.3,
            "ref_free": False,
            "speed": 1.0,
            "if_freeze": False,
            "sample_steps": 8,
            "if_sr": False,
            "pause_second": 0.3
        }

        try:
            logger.info("🚀 开始生成语音...")

            last_result = None
            for result in get_tts_wav(**tts_params):
                last_result = result

            if last_result is None:
                logger.error("❌ 没有获取到结果")
                return None

            sr, audio_data = last_result
            logger.info(f"采样率: {sr}, 音频形状: {audio_data.shape}")

            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            sf.write(output_path, audio_data, sr)

            if os.path.exists(output_path):
                logger.info(f"✅ 语音已保存到: {output_path}")
                return output_path
            else:
                logger.error("❌ 文件保存失败")
                return None

        except Exception as e:
            logger.error(f"❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
            return None