"""首页（以 Android Settings 为示例被测 APP）

演示 Page Object：元素定位 + 业务动作封装。
实际项目中将 com.android.settings 换成被测 APP 即可。
"""
import allure

from pages.base_page import BasePage, Locator


class HomePage(BasePage):
    # ---------- 元素定位 ----------
    SEARCH_BOX = Locator("resource_id", "com.android.settings:id/search_action_bar")  # Settings 搜索框
    SEARCH_INPUT = Locator("resource_id", "com.android.settings:id/search_input")
    SEARCH_RESULT_ITEM = Locator("resource_id", "com.android.settings:id/title")

    # ---------- 业务动作 ----------
    @allure.step("打开搜索")
    def open_search(self):
        if self.exists(self.SEARCH_BOX, timeout=3):
            self.click(self.SEARCH_BOX)

    @allure.step("搜索关键字: {keyword}")
    def search(self, keyword: str):
        if self.exists(self.SEARCH_INPUT, timeout=3):
            self.input(self.SEARCH_INPUT, keyword)
        else:
            # 部分版本直接点击搜索框后出现输入框
            self.click(self.SEARCH_BOX)
            self.input(self.SEARCH_INPUT, keyword)

    @allure.step("点击搜索结果: {title}")
    def click_result(self, title: str):
        item = Locator("text", title)
        self.click(item)

    @allure.step("获取搜索结果列表文本")
    def get_result_titles(self) -> list:
        # 找所有 title 元素文本
        titles = []
        try:
            els = self.d(resourceId="com.android.settings:id/title")
            for el in els:
                txt = el.get_text()
                if txt:
                    titles.append(txt)
        except Exception:
            pass
        return titles
