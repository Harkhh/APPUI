"""截图工具

- 通过 uiautomator2 截屏，保存到 reports/screenshots/。
- 自动 attach 到 Allure 报告。
"""
import os
import time

import allure

from utils.log_utils import get_logger

logger = get_logger()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "reports", "screenshots")


def take_screenshot(d, name: str = None, attach: bool = True) -> str:
    """对当前设备截图。

    Args:
        d: uiautomator2 Device。
        name: 截图文件名（不含扩展名）；None 则自动生成时间戳。
        attach: 是否同时 attach 到 Allure。

    Returns:
        截图文件绝对路径。
    """
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = f"{name or 'screenshot'}_{ts}.png"
    path = os.path.join(SCREENSHOT_DIR, fname)

    try:
        img = d.screenshot()
        with open(path, "wb") as f:
            img.save(f, "PNG")
        logger.info(f"截图已保存: {path}")
    except Exception as e:
        logger.error(f"截图失败: {e}")
        return ""

    if attach:
        attach_screenshot(path, name or "截图")
    return path


def attach_screenshot(path: str, name: str = "截图") -> None:
    """将已存在图片 attach 到 Allure。"""
    if not os.path.exists(path):
        logger.warning(f"截图不存在，跳过 attach: {path}")
        return
    try:
        allure.attach.file(path, name=name, attachment_type=allure.attachment_type.PNG)
    except Exception as e:
        logger.warning(f"Allure attach 失败: {e}")
