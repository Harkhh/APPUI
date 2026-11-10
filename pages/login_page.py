"""登录页（通用示例 PO）

注意：以 Android Settings 为示例 APP 时无登录页，本文件作为
通用 Page Object 编写示例。实际接入有登录功能的 APP 时，
只需修改下面的元素定位值即可。
"""
import allure

from pages.base_page import BasePage, Locator


class LoginPage(BasePage):
    # ---------- 元素定位（按真实 APP 调整 resource_id） ----------
    USERNAME_INPUT = Locator("resource_id", "com.demo.app:id/et_username")
    PASSWORD_INPUT = Locator("resource_id", "com.demo.app:id/et_password")
    LOGIN_BTN = Locator("resource_id", "com.demo.app:id/btn_login")
    WELCOME_TEXT = Locator("resource_id", "com.demo.app:id/tv_welcome")
    ERROR_TIP = Locator("resource_id", "com.demo.app:id/tv_error")

    # ---------- 业务动作 ----------
    @allure.step("输入用户名: {username}")
    def input_username(self, username: str):
        self.input(self.USERNAME_INPUT, username)

    @allure.step("输入密码: {password}")
    def input_password(self, password: str):
        self.input(self.PASSWORD_INPUT, password)

    @allure.step("点击登录按钮")
    def click_login(self):
        self.click(self.LOGIN_BTN)

    @allure.step("执行登录: {username}")
    def login(self, username: str, password: str):
        self.input_username(username)
        self.input_password(password)
        self.click_login()

    @allure.step("获取欢迎文案")
    def get_welcome_text(self) -> str:
        return self.get_text(self.WELCOME_TEXT)

    @allure.step("获取错误提示")
    def get_error_tip(self) -> str:
        if self.exists(self.ERROR_TIP, timeout=2):
            return self.get_text(self.ERROR_TIP)
        return ""
