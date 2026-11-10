"""BasePage - 页面对象基类

封装 uiautomator2 常用操作，统一处理：
- 元素定位（支持 resource_id / text / xpath / class 等多种策略）
- 显式等待与重试
- 点击 / 输入 / 滑动 / 截图
- 文本断言

所有 Page 类继承本类，元素定位通过 Locator 对象描述。
"""
import os
import time

import allure

from utils.log_utils import get_logger

logger = get_logger()


class Locator:
    """元素定位描述。

    strategy 取值：
        resource_id  -> d(resourceId=...)
        text         -> d(text=...)
        text_contains-> d(textContains=...)
        description  -> d(description=...)
        xpath        -> d.xpath(...)
        className    -> d(className=...)
    """

    def __init__(self, strategy: str, value: str, index: int = None):
        self.strategy = strategy
        self.value = value
        self.index = index

    @classmethod
    def from_dict(cls, d: dict) -> "Locator":
        """从 YAML dict 构造，如 {resource_id: "com.x:id/a"}。"""
        if not d:
            return None
        for key in ("resource_id", "text", "text_contains", "description", "xpath", "className", "class_name"):
            if key in d:
                strat = "text_contains" if key == "text_contains" else ("className" if key == "class_name" else key)
                return cls(strat, d[key], d.get("index"))
        raise ValueError(f"无法识别定位器: {d}")

    def __repr__(self):
        return f"Locator({self.strategy}={self.value!r}, index={self.index})"


class BasePage:
    """所有 Page 的基类。"""

    def __init__(self, d, request=None):
        self.d = d
        self.request = request

    # ---------- 元素查找 ----------
    def find(self, locator: Locator, timeout: float = None):
        """按 Locator 返回 u2 UiObject。"""
        obj = self._select(locator)
        timeout = timeout if timeout is not None else getattr(self.d, "_wait_timeout", 10)
        if not obj.wait(timeout=timeout):
            raise AssertionError(f"元素未找到: {locator} (超时 {timeout}s)")
        return obj

    def find_optional(self, locator: Locator, timeout: float = 3):
        """找元素，找不到返回 None（不抛异常）。"""
        obj = self._select(locator)
        return obj if obj.wait(timeout=timeout) else None

    def _select(self, locator: Locator):
        if locator.strategy == "resource_id":
            obj = self.d(resourceId=locator.value, index=locator.index) if locator.index is not None else self.d(resourceId=locator.value)
        elif locator.strategy == "text":
            obj = self.d(text=locator.value, index=locator.index) if locator.index is not None else self.d(text=locator.value)
        elif locator.strategy == "text_contains":
            obj = self.d(textContains=locator.value)
        elif locator.strategy == "description":
            obj = self.d(description=locator.value)
        elif locator.strategy == "xpath":
            obj = self.d.xpath(locator.value)
        elif locator.strategy in ("className",):
            obj = self.d(className=locator.value)
        else:
            raise ValueError(f"不支持的定位策略: {locator.strategy}")
        return obj

    # ---------- 基础动作 ----------
    @allure.step("点击元素 {locator}")
    def click(self, locator: Locator, timeout: float = None) -> None:
        self.find(locator, timeout).click()

    @allure.step("输入文本 {text}")
    def input(self, locator: Locator, text: str, clear: bool = True, timeout: float = None) -> None:
        el = self.find(locator, timeout)
        if clear:
            el.clear_text()
        el.set_text(text)

    @allure.step("获取元素文本")
    def get_text(self, locator: Locator, timeout: float = None) -> str:
        return self.find(locator, timeout).get_text()

    @allure.step("判断元素是否存在")
    def exists(self, locator: Locator, timeout: float = 3) -> bool:
        return self.find_optional(locator, timeout) is not None

    @allure.step("滑动: {direction}")
    def swipe(self, direction: str = "up", scale: float = 0.8) -> None:
        # u2 d.swipe_ext
        self.d.swipe_ext(direction=direction, scale=scale)

    def swipe_up(self):
        self.swipe("up")

    def swipe_down(self):
        self.swipe("down")

    def swipe_left(self):
        self.swipe("left")

    def swipe_right(self):
        self.swipe("right")

    @allure.step("按返回键")
    def press_back(self):
        self.d.press("back")

    @allure.step("按 home 键")
    def press_home(self):
        self.d.press("home")

    @allure.step("等待 {seconds}s")
    def sleep(self, seconds: float):
        time.sleep(seconds)

    # ---------- 断言 ----------
    @allure.step("断言元素文本为 {expected}")
    def assert_text(self, locator: Locator, expected: str, timeout: float = None):
        actual = self.get_text(locator, timeout)
        assert expected in actual, f"断言失败: 期望文本含 '{expected}', 实际='{actual}'"
        return True

    @allure.step("断言元素存在")
    def assert_exists(self, locator: Locator, timeout: float = 5):
        assert self.exists(locator, timeout), f"断言失败: 元素应存在 {locator}"

    @allure.step("断言元素不存在")
    def assert_not_exists(self, locator: Locator, timeout: float = 3):
        assert not self.exists(locator, timeout), f"断言失败: 元素不应存在 {locator}"

    # ---------- 截图 ----------
    def screenshot(self, name: str = "截图"):
        from utils.screenshot_utils import take_screenshot
        return take_screenshot(self.d, name=name)

    # ---------- APP 控制 ----------
    def launch_app(self, package_name: str, activity: str = None):
        from utils.driver_utils import DriverFactory
        DriverFactory.launch_app(self.d, package_name, activity)

    def stop_app(self, package_name: str):
        from utils.driver_utils import DriverFactory
        DriverFactory.stop_app(self.d, package_name)
