import logging
import os
import sys
import requests
from logging import Formatter, StreamHandler, Handler
from logging.handlers import RotatingFileHandler

from app.core import settings


os.makedirs(settings.LOG_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(filename)s.%(funcName)s:%(lineno)d | %(message)s"


# ----------------------------------------------------
# メインロガーの作成
# ----------------------------------------------------
def create_default_logger() -> logging.Logger:
    logger = logging.getLogger("default_logger")
    logger.setLevel(logging.DEBUG)

    console_handler = StreamHandler(sys.stdout)
    console_handler.setFormatter(Formatter(LOG_FORMAT))
    console_handler.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        settings.LOG_FILE_APP,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(Formatter(LOG_FORMAT))
    file_handler.setLevel(logging.DEBUG)

    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# ----------------------------------------------------
# Healthchecks.io用カスタムハンドラー
# ----------------------------------------------------
def _create_healthchecks_handler(slug: str) -> Handler:
    class HealthchecksHandler(Handler):
        def __init__(self, slug: str):
            super().__init__()
            self.slug = slug

            self.file_handler = RotatingFileHandler(
                settings.LOG_FILE_HC,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            self.file_handler.setFormatter(Formatter(LOG_FORMAT))

        def emit(self, record):
            try:
                if not settings.HEALTHCHECKS_BASE_URL or not settings.HEALTHCHECKS_PING_KEY:
                    # 設定が不完全な場合はファイルに記録
                    self.file_handler.emit(record)
                    return

                ping_url = f"{settings.HEALTHCHECKS_BASE_URL}/ping/{settings.HEALTHCHECKS_PING_KEY}/{settings.HEALTHCHECKS_SLUG_PREFIX}-{self.slug}"

                if record.levelno <= logging.DEBUG:
                    endpoint = ping_url + "/start"
                elif record.levelno <= logging.INFO:
                    endpoint = ping_url
                else:
                    endpoint = ping_url + "/fail"

                log_data = {
                    "level": record.levelname,
                    "filename": record.filename,
                    "function": record.funcName,
                    "line": record.lineno,
                    "timestamp": record.created,
                    "message": record.getMessage(),
                }

                response = requests.post(endpoint, json=log_data, timeout=5)
                response.raise_for_status()
            except Exception as e:
                # ヘルスチェック送信に失敗した場合、ファイルに記録
                failure_record = logging.LogRecord(
                    name=record.name,
                    level=logging.ERROR,
                    pathname=record.pathname,
                    lineno=record.lineno,
                    msg=f"Failed to send ping to Healthchecks (slug: {self.slug}): {record.getMessage()} | Error: {str(e)}",
                    args=(),
                    exc_info=None
                )
                failure_record.filename = record.filename
                failure_record.funcName = record.funcName
                failure_record.created = record.created

                self.file_handler.emit(failure_record)

    return HealthchecksHandler(slug)


# ----------------------------------------------------
# Healthchecks Loggerの作成
# ----------------------------------------------------
def create_healthchecks_logger(slug: str) -> logging.Logger:
    logger = logging.getLogger(f"hc_logger_{slug}")
    logger.setLevel(logging.DEBUG)

    healthcheck_handler = _create_healthchecks_handler(slug)
    healthcheck_handler.setLevel(logging.DEBUG)

    logger.handlers.clear()
    logger.addHandler(healthcheck_handler)

    return logger


# ----------------------------------------------------
# ロガーの初期化
# ----------------------------------------------------
main_logger = create_default_logger()
hc_hc_logger = create_healthchecks_logger("hc")
hc_def_logger = create_healthchecks_logger("def")
hc_err_logger = create_healthchecks_logger("err")
