"""设备驱动管理（uiautomator2）

负责设备连接、设置、APP 启停。封装为 DriverFactory，
在 conftest.py 中作为 fixture 提供，保证整个 session 复用同一驱动。
"""
import os

import uiautomator2 as u2

from utils.yaml_utils import load_yaml
from utils.log_utils import get_logger

logger = get_logger()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DriverFactory:
    """设备驱动工厂。"""

    @staticmethod
    def load_config() -> dict:
        return load_yaml(os.path.join(BASE_DIR, "config", "config.yaml"))

    @staticmethod
    def connect() -> u2.Device:
        """按 config.yaml 连接设备并完成初始化。"""
        cfg = DriverFactory.load_config().get("device", {})
        connect_type = cfg.get("connect_type", "usb")
        serial = cfg.get("serial", "")
        device_ip = cfg.get("device_ip", "")

        logger.info(f"连接设备: 方式={connect_type}, serial={serial or '自动'}, ip={device_ip or 'N/A'}")

        if connect_type == "wifi":
            if not device_ip:
                raise ValueError("wifi 连接需要在 config.yaml 设置 device_ip")
            d = u2.connect(device_ip)
        else:
            # USB 连接：serial 留空时 u2 自动选择第一个设备
            d = u2.connect(serial) if serial else u2.connect()

        # 应用 settings
        settings = cfg.get("settings", {})
        if settings:
            try:
                d.settings.update(settings)
            except Exception as e:
                logger.warning(f"应用 settings 失败(可忽略): {e}")

        # 打印设备信息，便于排查
        try:
            info = d.info
            logger.info(
                "设备就绪: {} | Android {} | {}".format(
                    info.get("productName", "?"),
                    info.get("sdkInt", "?"),
                    info.get("displaySizeDp", "?"),
                )
            )
        except Exception as e:
            logger.warning(f"读取设备 info 失败: {e}")

        if cfg.get("auto_init", True):
            try:
                d.implicitly_wait(cfg.get("settings", {}).get("wait_timeout", 10))
            except Exception:
                pass

        return d

    @staticmethod
    def launch_app(d: u2.Device, package_name: str, activity: str = None) -> None:
        """启动指定 APP。"""
        logger.info(f"启动 APP: {package_name} activity={activity or '自动'}")
        if activity:
            d.shell(f"am start -n {package_name}/{activity}")
        else:
            d.app_start(package_name)

    @staticmethod
    def stop_app(d: u2.Device, package_name: str) -> None:
        logger.info(f"停止 APP: {package_name}")
        try:
            d.app_stop(package_name)
        except Exception as e:
            logger.warning(f"停止 APP 失败: {e}")

    @staticmethod
    def clear_app(d: u2.Device, package_name: str) -> None:
        logger.info(f"清理 APP 数据: {package_name}")
        try:
            d.app_clear(package_name)
        except Exception as e:
            logger.warning(f"清理 APP 数据失败: {e}")
