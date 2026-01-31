from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union
from .config import CONFIG
from loguru import logger


_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

_FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: Union[str, int] = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_loguru(
    *,
    name: str = "app",
    level: str = "INFO",
    log_dir: Optional[Union[str, Path]] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    rotation: str = "10 MB",
    retention: str = "7 days",
    compression: str = "zip",
    enqueue: bool = True,
    backtrace: bool = False,
    diagnose: bool = False,
    intercept_logging: bool = True,
) -> "logger.__class__":
    env_level = os.getenv("LOG_LEVEL") or (CONFIG.get("log_level") if isinstance(CONFIG, dict) else None)
    if env_level:
        level = env_level
    level = level.upper()

    env_name = os.getenv("LOG_NAME")
    if env_name:
        name = env_name

    if log_dir is None:
        env_dir = os.getenv("LOG_DIR")
        log_dir_path = Path(env_dir) if env_dir else (Path.cwd() / "logs")
    else:
        log_dir_path = Path(log_dir)

    logger.remove()

    if enable_console:
        logger.add(
            sys.stderr,
            level=level,
            format=_CONSOLE_FORMAT,
            colorize=True,
            enqueue=enqueue,
            backtrace=backtrace,
            diagnose=diagnose,
        )

    if enable_file:
        log_dir_path.mkdir(parents=True, exist_ok=True)
        log_path = log_dir_path / f"{name}_{{time:YYYY-MM-DD}}.log"
        logger.add(
            str(log_path),
            level=level,
            format=_FILE_FORMAT,
            rotation=rotation,
            retention=retention,
            compression=compression,
            enqueue=enqueue,
            backtrace=backtrace,
            diagnose=diagnose,
            encoding="utf-8",
        )

    if intercept_logging:
        _configure_standard_logging(level)

    return logger


def _configure_standard_logging(level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers = [_InterceptHandler()]
    root_logger.setLevel(level)

    for _name, existing_logger in logging.root.manager.loggerDict.items():
        if isinstance(existing_logger, logging.Logger):
            existing_logger.handlers = []
            existing_logger.propagate = True


def get_logger() -> "logger.__class__":
    return logger
