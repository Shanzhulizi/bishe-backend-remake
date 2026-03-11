import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)


def _create_handler(filename: str, level=logging.INFO):
    handler = RotatingFileHandler(
        LOG_DIR / filename,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    return handler


def setup_logging():
    logging.getLogger().handlers.clear()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 控制台日志
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(LOG_FORMAT))

    # 文件日志
    app_handler = _create_handler("app.log", logging.INFO)
    error_handler = _create_handler("error.log", logging.ERROR)

    root_logger.addHandler(console)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
