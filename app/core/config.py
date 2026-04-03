from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


# print(f"加载配置，BASE_DIR={BASE_DIR}")

class Settings(BaseSettings):
    # API配置
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "AI角色扮演聊天平台"

    # 数据库配置
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # 异步数据库配置
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """异步数据库连接（使用 asyncpg）"""
        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite默认端口
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

    # JWT配置
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # DeepSeek配置

    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/chat/completions"
    DEEPSEEK_MODEL: str = "deepseek-chat"  # 或者 "deepseek-reasoner"

    # ========== Pydantic v2 配置 ==========
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    LOCAL_HOST: str = "http://localhost:8000"
    STATIC_DIR: str = "E:/Code/Python/AIChat/static"

    # 语音文件存储路径
    AUDIO_FILES_DIR: Path = BASE_DIR / "static" / "audio_files"


    # CosyVoice 源码路径（你的本地路径）
    COSYVOICE_PATH: Path = BASE_DIR / "CosyVoice"

    # CosyVoice 模型路径（你的本地模型路径）
    COSYVOICE_MODEL_DIR: Path = BASE_DIR / "models" / "iic" / "CosyVoice-300M"
    COSYVOICE2_MODEL_DIR: Path = BASE_DIR / "models" / "iic" / "CosyVoice2-0.5B"

    # CosyVoice 声音样本路径
    COSYVOICE_SAMPLE_DIR: Path = BASE_DIR / "static"/"cosyvoice" / "cosyvoice_sample"

    # CosyVoice 声音输出路径
    COSYVOICE_OUTPUT_DIR: Path = BASE_DIR / "static"/"cosyvoice" / "cosyvoice_output"
    COSYVOICE2_OUTPUT_DIR: Path = BASE_DIR / "static" /"cosyvoice"/ "cosyvoice2_output"



    AVATAR_IMAGES_DIR: Path = BASE_DIR / "static" / "avatars"


    GPT_SoVITS_OUTPUT_DIR: Path = BASE_DIR / "static" / "voice"/"gpt_sovits_output"
    PROMPT_VOICE_DIR: Path = BASE_DIR / "static" / "voice" / "prompt_voice"


    # HF_CACHE_DIR: Path = BASE_DIR / "models" / "hf_cache"
    #
    # ETHICS_MODEL_DIR: Path = BASE_DIR / "models" / "ethics"

settings = Settings()
