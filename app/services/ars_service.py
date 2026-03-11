import os
import tempfile
import time
from typing import Tuple

from faster_whisper import WhisperModel


class ASRService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = WhisperModel(
                "../models/faster-whisper-medium",
                # model_size_or_path="medium",
                device="cuda",
                compute_type="float16"
            )
        return cls._model

    @classmethod
    async def speech_to_text(
            cls,
            audio_data: bytes,
            lang: str = "zh"
    ) -> Tuple[str, float]:
        start = time.time()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_data)
            tmp_path = f.name

        model = cls.get_model()
        segments, info = model.transcribe(
            tmp_path,
            language=lang,
            vad_filter=True
        )

        text = "".join([seg.text for seg in segments])
        duration = time.time() - start

        os.unlink(tmp_path)

        return text, duration
