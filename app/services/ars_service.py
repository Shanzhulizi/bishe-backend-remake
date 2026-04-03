import asyncio
import os
import tempfile
import time
from typing import Tuple

from faster_whisper import WhisperModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class ASRService:
    _model = None
    _executor = None  # 线程池执行器

    @classmethod
    def _get_executor(cls):
        """获取线程池执行器（延迟初始化）"""
        if cls._executor is None:
            import concurrent.futures
            cls._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        return cls._executor

    @classmethod
    def _get_model_sync(cls):
        """同步获取模型（在线程池中执行）"""
        if cls._model is None:
            logger.info("正在加载 Whisper 模型...")
            cls._model = WhisperModel(
                "../models/faster-whisper-medium",
                device="cuda",
                compute_type="float16"
            )
            logger.info("Whisper 模型加载完成")
        return cls._model

    @classmethod
    def _transcribe_sync(cls, audio_path: str, lang: str) -> Tuple[str, float]:
        """同步转写（在线程池中执行）"""
        start = time.time()

        model = cls._get_model_sync()
        segments, info = model.transcribe(
            audio_path,
            language=lang,
            vad_filter=True
        )

        text = "".join([seg.text for seg in segments])
        duration = time.time() - start

        logger.info(f"ASR 完成: 时长={duration:.2f}s, 语言={info.language}, 文本长度={len(text)}")

        return text, duration

    @classmethod
    async def speech_to_text(
            cls,
            audio_data: bytes,
            lang: str = "zh"
    ) -> Tuple[str, float]:
        """
        异步语音识别

        Args:
            audio_data: 音频数据（字节）
            lang: 语言代码

        Returns:
            (识别的文本, 耗时秒数)
        """
        loop = asyncio.get_event_loop()
        executor = cls._get_executor()

        # 1. 写入临时文件（同步 I/O）
        def _write_temp_file():
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio_data)
                return f.name

        try:
            # 在线程池中写入临时文件
            tmp_path = await loop.run_in_executor(executor, _write_temp_file)
            logger.debug(f"临时音频文件: {tmp_path}")

            # 2. 在线程池中执行转写（耗时操作）
            text, duration = await loop.run_in_executor(
                executor,
                cls._transcribe_sync,
                tmp_path,
                lang
            )

            return text, duration

        except Exception as e:
            logger.error(f"ASR 识别失败: {e}")
            raise

        finally:
            # 3. 在线程池中删除临时文件
            if 'tmp_path' in locals():
                def _delete_file():
                    try:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {e}")

                await loop.run_in_executor(executor, _delete_file)

    @classmethod
    async def close(cls):
        """关闭线程池（应用关闭时调用）"""
        if cls._executor:
            cls._executor.shutdown(wait=True)
            cls._executor = None
            logger.info("ASR 线程池已关闭")