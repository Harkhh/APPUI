"""日志工具（基于 loguru）

- 日志文件统一输出到 logs/ 目录，与测试报告目录完全分离。
- 提供单例 logger，全项目复用。
"""
import os
import sys

from loguru import logger

from utils.yaml_utils import load_yaml

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")


def _setup_logger():
    """根据 config/logging.yaml 初始化 loguru。"""
    os.makedirs(LOG_DIR, exist_ok=True)
    cfg = load_yaml(os.path.join(BASE_DIR, "config", "logging.yaml")).get("log", {})
    level = cfg.get("level", "INFO")
    fmt = cfg.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {file}:{line} | {message}")

    logger.remove()
    if cfg.get("console", True):
        logger.add(sys.stderr, level=level, format=fmt, enqueue=True)
    if cfg.get("file", True):
        logger.add(
            os.path.join(LOG_DIR, "run_{time:YYYY-MM-DD}.log"),
            level=level,
            format=fmt,
            rotation=cfg.get("rotation", "10 MB"),
            retention=cfg.get("retention", "7 days"),
            compression=cfg.get("compression", "zip"),
            encoding=cfg.get("encoding", "utf-8"),
            enqueue=True,
        )
    return logger


# 全局单例
my_logger = _setup_logger()


def get_logger():
    """返回全局 logger 单例。"""
    return my_logger
