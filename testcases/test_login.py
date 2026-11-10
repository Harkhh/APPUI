"""pytest 脚本用例示例 - 登录功能

演示要点：
- 参数化（直接内联 + 外部 Excel 数据分离两种方式）
- 优先级 / 冒烟标记
- 登录页 Page Object 调用
- 数据驱动断言

注意：示例 APP 为 Android Settings（无登录页），运行时元素会找不到，
本文件主要演示「脚本用例 + 数据分离 + 标记」的编写范式。
真实接入有登录的 APP 后，只需改 LoginPage 的元素定位即可直接复用。
"""
import os

import allure
import pytest

from pages.login_page import LoginPage
from utils.excel_utils import read_excel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 业务数据分离方式一：Excel 读取（data/login_data.xlsx 首行为表头）
LOGIN_DATA = read_excel(os.path.join(BASE_DIR, "data", "login_data.xlsx"), sheet="登录用例") \
    if os.path.exists(os.path.join(BASE_DIR, "data", "login_data.xlsx")) else []

# 方式二：内联数据（适合少量正向/反向用例）
LOGIN_INLINE = [
    {"id": "正向", "username": "admin", "password": "123456", "expect_success": True},
    {"id": "反向-密码错", "username": "admin", "password": "wrong", "expect_success": False},
]


@allure.epic("登录模块")
@allure.feature("账号登录")
class TestLogin:
    """登录功能用例。"""

    @allure.story("正向登录")
    @allure.severity("critical")
    @pytest.mark.smoke
    @pytest.mark.P0
    @pytest.mark.parametrize("case", LOGIN_INLINE, ids=[c["id"] for c in LOGIN_INLINE])
    def test_login_inline(self, d, app, case):
        """内联数据驱动登录。"""
        login = LoginPage(d)
        login.launch_app(app)
        with allure.step(f"登录: {case['username']}"):
            login.login(case["username"], case["password"])
        with allure.step("校验登录结果"):
            if case["expect_success"]:
                assert login.exists(login.WELCOME_TEXT, timeout=8), "应进入欢迎页"
                assert "欢迎" in login.get_welcome_text()
            else:
                err = login.get_error_tip()
                assert err, "应有错误提示"

    @allure.story("Excel 数据驱动登录")
    @allure.severity("normal")
    @pytest.mark.P1
    @pytest.mark.regression
    @pytest.mark.skipif(not LOGIN_DATA, reason="未提供 data/login_data.xlsx")
    @pytest.mark.parametrize("case", LOGIN_DATA, ids=[str(c.get("id", c.get("username", ""))) for c in LOGIN_DATA])
    def test_login_from_excel(self, d, app, case):
        """Excel 数据驱动登录，每行一条用例。"""
        login = LoginPage(d)
        login.launch_app(app)
        login.login(case.get("username", ""), case.get("password", ""))
        if str(case.get("expect_success", "")).lower() in ("true", "1", "yes"):
            assert login.exists(login.WELCOME_TEXT, timeout=8)
        else:
            assert login.get_error_tip()
