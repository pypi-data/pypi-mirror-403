import logging.config
import os
import sys
from pathlib import Path

QWAK_DIR_PATH: Path = Path.home() / ".qwak"

log_level = (
    "DEBUG"
    if os.getenv("QWAK_DEBUG", "false").casefold() == "true".casefold()
    else "INFO"
)
os.makedirs(QWAK_DIR_PATH, exist_ok=True)
log_file: str = os.path.join(QWAK_DIR_PATH, "qwak-log-history.log")

DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(levelname)s - %(name)s.%(module)s.%(funcName)s:%(lineno)d - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": log_file,
        },
    },
    "loggers": {
        __name__: {
            "level": log_level,
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

if os.getenv("IS_LOGGER_SHADED") is not None:
    logger = logging.getLogger(__name__)
else:
    logging.config.dictConfig(DEFAULT_LOGGING)
    logger = logging.getLogger(__name__)
