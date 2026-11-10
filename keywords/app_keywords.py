"""APP 操作关键字引擎

核心方法 execute_step(step_dict) 根据步骤中的 keyword 字段，
分发到对应动作。YAML 用例的 steps 即由此驱动执行。

支持的关键字清单（详见 README「关键字清单」）：
    launch_app / stop_app / clear_app
    click / long_click / input / clear_input
    get_text / assert_text / assert_exists / assert_not_exists
    swipe_up / swipe_down / swipe_left / swipe_right / swipe_to
    press_back / press_home / sleep / wait
    screenshot / toast_assert
"""
import time

import allure

from pages.base_page import BasePage, Locator
from utils.log_utils import get_logger
from utils.screenshot_utils import take_screenshot

logger = get_logger()


class AppKeywords(BasePage):
    """关键字引擎，继承 BasePage 复用基础能力，增加关键字分发。"""

    def __init__(self, d, request=None):
        super().__init__(d, request)
        # 上下文：存放 get_text 等结果，供后续断言使用
        self._ctx = {}

    def execute_step(self, step: dict):
        """执行单条步骤。

        step 结构:
            keyword: click            # 必填
            locator: {resource_id: ...}  # 视关键字
            text: xxx
            expected: xxx
            seconds: 3
            package: com.x
            name: 截图名
            description: 步骤说明       # 仅用于 Allure step 标题（已在 loader 包裹）
        """
        kw = step.get("keyword")
        if not kw:
            raise ValueError(f"步骤缺少 keyword 字段: {step}")
        handler = self._handlers().get(kw)
        if handler is None:
            raise ValueError(f"不支持的关键字: {kw}（步骤: {step}）")
        handler(step)

    # ---------- 关键字分发表 ----------
    def _handlers(self):
        return {
            # APP 控制
            "launch_app": self._kw_launch_app,
            "stop_app": self._kw_stop_app,
            "clear_app": self._kw_clear_app,
            # 基础操作
            "click": self._kw_click,
            "long_click": self._kw_long_click,
            "input": self._kw_input,
            "clear_input": self._kw_clear_input,
            "get_text": self._kw_get_text,
            # 滑动
            "swipe_up": self._kw_swipe_up,
            "swipe_down": self._kw_swipe_down,
            "swipe_left": self._kw_swipe_left,
            "swipe_right": self._kw_swipe_right,
            "swipe_to": self._kw_swipe_to,
            # 按键
            "press_back": self._kw_press_back,
            "press_home": self._kw_press_home,
            # 等待
            "sleep": self._kw_sleep,
            "wait": self._kw_wait,
            # 断言
            "assert_text": self._kw_assert_text,
            "assert_exists": self._kw_assert_exists,
            "assert_not_exists": self._kw_assert_not_exists,
            "toast_assert": self._kw_toast_assert,
            # 截图
            "screenshot": self._kw_screenshot,
        }

    # ===== 关键字实现 =====
    def _kw_launch_app(self, step):
        from utils.driver_utils import DriverFactory
        pkg = step.get("package") or self._app_package()
        DriverFactory.launch_app(self.d, pkg, step.get("activity"))

    def _kw_stop_app(self, step):
        from utils.driver_utils import DriverFactory
        DriverFactory.stop_app(self.d, step.get("package") or self._app_package())

    def _kw_clear_app(self, step):
        from utils.driver_utils import DriverFactory
        DriverFactory.clear_app(self.d, step.get("package") or self._app_package())

    def _kw_click(self, step):
        self.click(self._loc(step))

    def _kw_long_click(self, step):
        el = self.find(self._loc(step))
        el.long_click()

    def _kw_input(self, step):
        self.input(self._loc(step), step.get("text", ""))

    def _kw_clear_input(self, step):
        el = self.find(self._loc(step))
        el.clear_text()
        el.set_text(step.get("text", ""))

    def _kw_get_text(self, step):
        key = step.get("store", "last_text")
        self._ctx[key] = self.get_text(self._loc(step))

    def _kw_swipe_up(self, step):
        self.swipe_up()

    def _kw_swipe_down(self, step):
        self.swipe_down()

    def _kw_swipe_left(self, step):
        self.swipe_left()

    def _kw_swipe_right(self, step):
        self.swipe_right()

    def _kw_swipe_to(self, step):
        """向某方向滑动直到元素出现。"""
        loc = self._loc(step)
        direction = step.get("direction", "up")
        max_times = int(step.get("max_times", 5))
        for _ in range(max_times):
            if self.exists(loc, timeout=1):
                return
            self.swipe(direction)
        assert self.exists(loc, timeout=2), f"swipe_to 未找到元素: {loc}"

    def _kw_press_back(self, step):
        self.press_back()

    def _kw_press_home(self, step):
        self.press_home()

    def _kw_sleep(self, step):
        time.sleep(float(step.get("seconds", 1)))

    def _kw_wait(self, step):
        timeout = float(step.get("seconds", step.get("timeout", 5)))
        if step.get("locator"):
            self.find(self._loc(step), timeout=timeout)
        else:
            time.sleep(timeout)

    def _kw_assert_text(self, step):
        expected = step.get("expected", "")
        actual = self.get_text(self._loc(step))
        assert expected in actual, f"断言失败: 期望含 '{expected}', 实际='{actual}'"

    def _kw_assert_exists(self, step):
        self.assert_exists(self._loc(step))

    def _kw_assert_not_exists(self, step):
        self.assert_not_exists(self._loc(step))

    def _kw_toast_assert(self, step):
        expected = step.get("expected", "")
        # u2 2.x: d.toast.get_message / d.toast.show
        msg = ""
        for _ in range(5):
            try:
                msg = self.d.toast.get_message(timeout=2)
                if msg:
                    break
            except Exception:
                pass
        assert expected in (msg or ""), f"toast 断言失败: 期望含 '{expected}', 实际='{msg}'"

    def _kw_screenshot(self, step):
        take_screenshot(self.d, name=step.get("name", "步骤截图"))

    # ---------- 辅助 ----------
    def _loc(self, step) -> Locator:
        loc_dict = step.get("locator")
        if loc_dict is None:
            raise ValueError(f"步骤缺少 locator: {step}")
        return Locator.from_dict(loc_dict)

    def _app_package(self) -> str:
        """从 config 取默认包名。"""
        from utils.driver_utils import DriverFactory
        cfg = DriverFactory.load_config().get("app", {})
        return cfg.get("package_name", "")
