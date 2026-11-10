"""pytest 脚本用例示例 - Settings 首页搜索

演示：
- 参数化（@pytest.mark.parametrize + 外部 YAML 数据分离）
- 优先级 / 冒烟标记
- Page Object 调用
- Allure 分层标注（epic/feature/story/step）
- 失败截图由 conftest 自动处理，无需手写
"""
import os

import allure
import pytest

from pages.home_page import HomePage
from utils.yaml_utils import load_case_data

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 业务数据分离：从 data/search_data.yaml 读取参数化数据
SEARCH_DATA = load_case_data(os.path.join(BASE_DIR, "data", "search_data.yaml"), "search_cases")


@allure.epic("Android 设置 APP")
@allure.feature("首页搜索")
class TestHomeSearch:
    """首页搜索功能验证。"""

    @allure.story("搜索结果校验")
    @allure.severity("critical")
    @pytest.mark.smoke
    @pytest.mark.P0
    @pytest.mark.parametrize("case", SEARCH_DATA, ids=[c.get("id", c.get("keyword", "")) for c in SEARCH_DATA])
    def test_search(self, d, app, case):
        """参数化搜索：用 keyword 在 Settings 中搜索，校验结果。"""
        home = HomePage(d)
        with allure.step("启动 Settings 并打开搜索"):
            home.launch_app(app)
            home.open_search()
        with allure.step(f"输入关键字: {case.get('keyword')}"):
            home.search(case["keyword"])
            home.sleep(1)
        with allure.step("校验搜索结果包含期望项"):
            titles = home.get_result_titles()
            expected = case.get("expect_in_results", True)
            keyword = case["keyword"]
            if expected:
                assert any(keyword in t for t in titles), f"搜索 '{keyword}' 无结果: {titles}"
            else:
                assert not all(keyword in t for t in titles), "不应有结果"
            # 附加过程截图（成功也截图）
            home.screenshot(name=f"搜索_{keyword}")

    @allure.story("返回键退出搜索")
    @allure.severity("normal")
    @pytest.mark.P1
    @pytest.mark.regression
    def test_back_exit_search(self, d, app):
        """按返回键退出搜索。"""
        home = HomePage(d)
        home.launch_app(app)
        home.open_search()
        home.search("蓝牙")
        home.sleep(1)
        home.press_back()
        with allure.step("校验已退出搜索"):
            # 退出后搜索框恢复初始态
            assert home.exists(HomePage.SEARCH_BOX, timeout=5)
            home.screenshot(name="返回后首页")
