# APP UI 自动化测试框架

> 技术栈：Python 3.8+ · uiautomator2 (UI2) · pytest · Allure
>
> 面向 Android 原生/Hybrid APP 的 UI 自动化测试框架。支持参数化、业务数据分离、测试过程监测、冒烟/优先级配置、YAML/Excel 零代码用例、失败自动截图、日志与报告分目录、Allure 中文报告可定制。

---

## 目录

1. [功能特性](#1-功能特性)
2. [项目结构](#2-项目结构)
3. [环境准备与安装](#3-环境准备与安装)
4. [配置文件说明](#4-配置文件说明)
5. [运行方式](#5-运行方式)
6. [用例编写规范](#6-用例编写规范)
7. [关键字清单](#7-关键字清单)
8. [Allure 报告定制](#8-allure-报告定制)
9. [测试过程监测](#9-测试过程监测)
10. [常见问题 FAQ](#10-常见问题-faq)

---

## 1. 功能特性

| 需求 | 实现方式 |
|------|----------|
| ① 参数化 | pytest `@parametrize`；YAML `data` 字段；Excel 表格行 |
| ② 业务数据分离 | `data/` 目录独立存放 YAML/Excel，脚本通过工具读取，代码与数据解耦 |
| ③ 测试过程监测 | `utils/monitor.py` 钩子实时打印用例状态 + 汇总 `reports/summary.json` |
| ④ 冒烟/优先级配置 | pytest mark（`smoke / P0 / P1 / P2 / P3`）；`--priority` 命令行过滤；Allure severity 自动映射 |
| ⑤ YAML/Excel 用例 | `testcases/yaml_cases/*.yaml` 关键字驱动，`test_yaml_runner.py` 自动注入；Excel 经 `read_excel` 参数化 |
| ⑥ 失败截图 | `conftest.py` 的 `pytest_runtest_makereport` hook 自动截图并 attach 到 Allure |
| ⑦ 日志与报告分目录 | `logs/` 仅存日志；`reports/` 存 Allure 结果/HTML/截图/summary |
| ⑧ 中文报告 + YAML 定制 | `config/allure_config.yaml` 预配置标题/环境信息/缺陷分类，`run.py` 自动生成 `environment.properties` 等 |

---

## 2. 项目结构

```
APPUI/
├── config/                       # 配置文件（集中管理，改配置不改代码）
│   ├── config.yaml               # 主配置：设备/APP/超时/路径/用例过滤/监测
│   ├── allure_config.yaml        # Allure 报告中文定制：标题/环境/分类/severity
│   └── logging.yaml              # 日志配置（loguru）
├── data/                         # 业务测试数据（与脚本分离）
│   ├── search_data.yaml          #   YAML 参数化数据
│   └── login_data.xlsx           #   Excel 参数化数据（由 scripts/gen_login_excel.py 生成）
├── keywords/                     # 关键字驱动层（支撑 YAML 用例）
│   └── app_keywords.py           #   AppKeywords：execute_step 分发到各关键字
├── pages/                        # 页面对象层（Page Object 模式）
│   ├── base_page.py              #   BasePage + Locator：封装 u2 通用操作
│   ├── home_page.py              #   首页 PO（Settings 搜索示例）
│   └── login_page.py             #   登录页 PO（通用示例）
├── testcases/                    # 测试用例
│   ├── test_home.py              #   pytest 脚本用例（Settings 搜索）
│   ├── test_login.py             #   pytest 脚本用例（登录，内联+Excel双数据源）
│   ├── test_yaml_runner.py       #   YAML 用例自动运行器（注入 yaml_cases）
│   └── yaml_cases/               #   YAML 用例目录（新增 .yaml 即生效）
│       ├── test_search.yaml
│       └── test_login.yaml
├── utils/                        # 工具层
│   ├── yaml_utils.py             #   YAML 读写 + 用例数据加载
│   ├── excel_utils.py            #   Excel 读取为 list[dict]
│   ├── log_utils.py             #   loguru 日志单例（输出到 logs/）
│   ├── driver_utils.py           #   DriverFactory：u2 设备连接/启停 APP
│   ├── screenshot_utils.py       #   截图 + Allure attach
│   ├── allure_utils.py           #   Allure 元数据生成（environment/categories/executor）
│   ├── monitor.py                #   测试过程监测器（单例 + summary.json）
│   └── case_loader.py            #   YAML 用例 -> pytest 函数的动态加载器
├── scripts/                      # 辅助脚本
│   └── gen_login_excel.py        #   生成示例 Excel 数据
├── logs/                         # 日志目录（运行产物，自动生成）
├── reports/                      # 报告目录（运行产物，自动生成）
│   ├── allure-results/           #   Allure 原始结果
│   ├── allure-html/              #   Allure HTML 报告
│   ├── screenshots/              #   截图文件
│   └── summary.json              #   运行汇总
├── conftest.py                   # pytest 全局：fixtures + 失败截图hook + mark注册 + 监测
├── pytest.ini                    # pytest 配置
├── run.py                        # 运行入口（命令行 + Allure 报告生成）
├── requirements.txt             # 依赖清单
└── README.md                     # 本手册
```

**分层设计**：`用例层 → 关键字/页面对象层 → 工具层 → 设备驱动`

---

## 3. 环境准备与安装

### 3.1 系统要求
- Python 3.8+
- Android 设备（真机/模拟器），已开启「USB 调试」
- ADB 环境（`adb` 命令可用）
- Node.js（uiautomator2 首次会自动安装 atx-agent，需 adb 通信）

### 3.2 安装步骤

```bash
# 1. 进入项目根目录
cd Demo7

# 2. 创建并激活虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 Allure 命令行（生成 HTML 报告所需）
brew install allure               # macOS
# Windows: 下载 https://github.com/allure-framework/allure2/releases 解压并加入 PATH

# 5.（可选）初始化设备 atx-agent
python -m uiautomator2 init       # 对已连接设备初始化
# 或在 config.yaml 中 device.auto_init=true，运行时自动处理

# 6. 验证
python -m pytest --collect-only   # 应收集到 17 条用例
```

### 3.3 连接设备

USB 连接（默认）：
```bash
adb devices                       # 确认设备在线
```
WiFi 连接：在 `config/config.yaml` 中设置 `device.connect_type: wifi` 与 `device_ip`。

---

## 4. 配置文件说明

### 4.1 `config/config.yaml`（主配置）
关键字段：

| 字段 | 说明 |
|------|------|
| `device.connect_type` | `usb` / `wifi` |
| `device.serial` | 设备序列号，留空自动取第一个 |
| `device.settings.wait_timeout` | 元素等待超时（秒） |
| `app.package_name` | 被测 APP 包名（示例为 `com.android.settings`） |
| `app.restart_per_case` | 是否每条用例前重启 APP |
| `timing.retry_times` | 全局失败重试次数 |
| `path.*` | 各产物目录，日志与报告已分离 |
| `case_filter.mark` | 默认 mark 过滤（留空=全跑） |
| `monitor.*` | 过程监测开关与汇总文件 |

### 4.2 `config/allure_config.yaml`（报告定制）
详见 [第 8 节](#8-allure-报告定制)。

### 4.3 `config/logging.yaml`（日志）
控制日志级别、格式、轮转、保留期。日志文件输出到 `logs/run_YYYY-MM-DD.log`。

---

## 5. 运行方式

### 5.1 通过 `run.py`（推荐）

```bash
# 全量运行 + 自动生成 Allure 报告
python run.py

# 仅冒烟用例
python run.py -m smoke

# 仅 P0 优先级
python run.py --priority P0

# 按用例名关键字匹配
python run.py -k search

# 仅运行 YAML 用例
python run.py --yaml-only

# 失败重试 2 次
python run.py --reruns 2

# 直接打开报告（allure serve）
python run.py --allure-serve

# 指定单个用例文件
python run.py testcases/test_home.py

# 不生成 HTML 报告（仅跑测试）
python run.py --no-report
```

运行结束后：
- 控制台输出实时用例状态
- `reports/allure-html/index.html` 为中文报告
- `reports/summary.json` 为执行汇总
- `logs/run_*.log` 为过程日志

### 5.2 直接用 pytest

```bash
python -m pytest                              # 跑全部
python -m pytest -m smoke                     # 冒烟
python -m pytest --priority P0                # P0
python -m pytest testcases/test_home.py -v    # 指定文件
python -m pytest -k "search and not wifi"     # 表达式过滤
```

### 5.3 生成/查看报告

```bash
# 生成 HTML 报告（run.py 默认已执行）
allure generate reports/allure-results -o reports/allure-html --clean

# 本地打开报告
allure open reports/allure-html
# 或直接打开 reports/allure-html/index.html
```

---

## 6. 用例编写规范

框架支持 **三种** 用例编写方式，按复杂度递增：

### 6.1 方式一：YAML 关键字用例（推荐，零代码）

在 `testcases/yaml_cases/` 下新建 `test_xxx.yaml`，**无需改任何 Python 代码**，`test_yaml_runner.py` 会自动加载。

**文件结构**（每个 `- ` 列表项为一条用例）：

```yaml
- case_name: test_yaml_用例名       # 必须 test_ 开头，否则不被 pytest 收集
  feature: 功能模块                  # Allure feature
  story: 子场景                      # Allure story
  severity: P0                       # P0/P1/P2/P3 -> 自动映射 Allure severity
  marks: [smoke, P0]                 # pytest mark 列表
  description: 用例说明文字
  data:                              # 参数化数据（每行一个 dict）
    - id: 数据1
      user: admin
      pwd: "123456"
  steps:                             # 步骤列表，按 keyword 编排
    - keyword: launch_app
      description: 启动 APP
    - keyword: input
      description: 输入用户名 ${user}   # ${var} 引用 data 中的值
      locator: { resource_id: "com.demo.app:id/et_username" }
      text: "${user}"
    - keyword: click
      locator: { resource_id: "com.demo.app:id/btn_login" }
    - keyword: assert_text
      locator: { resource_id: "com.demo.app:id/tv_welcome" }
      expected: 欢迎
    - keyword: screenshot
      name: 登录结果_${user}
```

**locator 定位写法**（YAML dict，选其一）：

```yaml
locator: { resource_id: "com.x:id/btn" }     # 按 ID
locator: { text: "登录" }                    # 按文本
locator: { text_contains: "登录" }          # 按文本包含
locator: { description: "登录按钮" }         # 按 content-desc
locator: { xpath: "//android.widget.TextView[@text='登录']" }
locator: { className: "android.widget.Button" }
```

完整示例见 `testcases/yaml_cases/test_search.yaml` 与 `test_login.yaml`。

> ⚠️ 注意：在 `{ }` 流映射内，含 `${var}` 的值必须加引号（如 `text: "${var}"`），否则 YAML 解析报错。块级（不在 `{}` 内）的 `${var}` 可不加引号。

### 6.2 方式二：Excel 数据驱动用例

适合需要业务人员维护、表格化场景。在 `data/xxx.xlsx` 中：

| id | username | password | expect_success |
|----|----------|----------|----------------|
| 正向-admin | admin | 123456 | TRUE |
| 反向-密码错 | admin | wrongpwd | FALSE |

脚本侧读取：

```python
from utils.excel_utils import read_excel

LOGIN_DATA = read_excel("data/login_data.xlsx", sheet="登录用例")

@pytest.mark.parametrize("case", LOGIN_DATA, ids=[c["id"] for c in LOGIN_DATA])
def test_login(d, app, case):
    ...
```

生成示例 Excel：`python scripts/gen_login_excel.py`

### 6.3 方式三：pytest 脚本用例（复杂流程）

适合需要条件分支、复杂数据处理、多页面交互的场景。示例见 `testcases/test_home.py`：

```python
import allure
import pytest
from pages.home_page import HomePage
from utils.yaml_utils import load_case_data

SEARCH_DATA = load_case_data("data/search_data.yaml", "search_cases")

@allure.epic("Android 设置 APP")
@allure.feature("首页搜索")
class TestHomeSearch:
    @allure.story("搜索结果校验")
    @allure.severity("critical")
    @pytest.mark.smoke
    @pytest.mark.P0
    @pytest.mark.parametrize("case", SEARCH_DATA, ids=[c["id"] for c in SEARCH_DATA])
    def test_search(self, d, app, case):
        home = HomePage(d)
        home.launch_app(app)
        home.search(case["keyword"])
        ...
```

**可用 fixtures**（由 `conftest.py` 提供）：
- `d` —— uiautomator2 设备（session 级复用）
- `app` —— 启动被测 APP，返回包名

### 6.4 编写新 Page Object

继承 `BasePage`，定义元素 `Locator` 与业务方法：

```python
from pages.base_page import BasePage, Locator
import allure

class ProfilePage(BasePage):
    AVATAR = Locator("resource_id", "com.x:id/avatar")

    @allure.step("进入个人资料")
    def open_profile(self):
        self.click(self.AVATAR)
```

`BasePage` 提供方法：`click / input / get_text / exists / swipe / press_back / assert_text / assert_exists / screenshot / launch_app` 等。

---

## 7. 关键字清单

YAML 用例 `steps` 中可用的 `keyword`：

| 关键字 | 必填参数 | 说明 |
|--------|----------|------|
| `launch_app` | package(可选,默认config) | 启动 APP |
| `stop_app` | package(可选) | 停止 APP |
| `clear_app` | package(可选) | 清除 APP 数据 |
| `click` | locator | 点击元素 |
| `long_click` | locator | 长按元素 |
| `input` | locator, text | 输入文本（不清空） |
| `clear_input` | locator, text | 清空后输入 |
| `get_text` | locator, store(可选) | 获取文本存入上下文 |
| `swipe_up` / `swipe_down` / `swipe_left` / `swipe_right` | — | 四向滑动 |
| `swipe_to` | locator, direction, max_times | 滑动直到元素出现 |
| `press_back` | — | 返回键 |
| `press_home` | — | Home 键 |
| `sleep` | seconds | 固定等待 |
| `wait` | locator(可选), seconds | 等元素出现/固定等待 |
| `assert_text` | locator, expected | 断言元素文本含期望值 |
| `assert_exists` | locator | 断言元素存在 |
| `assert_not_exists` | locator | 断言元素不存在 |
| `toast_assert` | expected | 断言 Toast 文案 |
| `screenshot` | name | 截图并 attach 到 Allure |

所有关键字均可带 `description` 字段，作为 Allure 步骤标题展示。

---

## 8. Allure 报告定制

报告页面内容通过 `config/allure_config.yaml` 预配置，`run.py` / `conftest.py` 会自动生成 Allure 元数据文件，**无需手改报告目录**。

### 8.1 中文标题与环境信息

```yaml
title: "APP UI 自动化测试报告"          # 报告页标题
language: "zh"                          # 中文界面
subtitle: "Android 自动化测试结果总览"

environment:                            # 顶部「Environment」信息
  项目名称: "APP UI 自动化测试框架"
  测试平台: "Android (uiautomator2)"
  测试执行人: "QA Team"
  # 运行时还会自动追加 APP 包名、设备连接方式
```

生成产物：`reports/allure-results/environment.properties`

### 8.2 缺陷分类（Categories）

```yaml
categories:
  - name: "断言失败"
    matchedStatuses: ["failed"]
    messageRegex: "AssertionError.*"
  - name: "元素未找到/超时"
    matchedStatuses: ["failed", "broken"]
    messageRegex: ".*[Tt]imeout|NotFound.*"
```

生成产物：`reports/allure-results/categories.json`，报告会按失败原因自动归类。

### 8.3 优先级展示映射

```yaml
severity_map:
  blocker: "阻塞 (P0)"
  critical: "关键 (P0)"
  normal: "常规 (P1)"
  minor: "次要 (P2)"
  trivial: "轻微 (P3)"
```

YAML 用例写 `severity: P0`，loader 自动转 Allure `severity=critical`，报告按优先级分组。

### 8.4 执行信息

`executor.json` 自动写入执行器名称与构建号，便于 CI 集成追溯。

---

## 9. 测试过程监测

由 `utils/monitor.py` 实现，在 `conftest.py` 中通过钩子接入：

- **实时打印**：每条用例「开始 / 通过 / 失败 / 跳过」均输出到日志与控制台，含耗时。
- **汇总文件**：运行结束生成 `reports/summary.json`，结构：
  ```json
  {
    "total": 17,
    "counts": {"passed": 15, "failed": 2, "skipped": 0, "error": 0, "rerun": 0},
    "duration_seconds": 128.5,
    "start_time": "2026-10-12 16:00:00",
    "records": [{"nodeid": "...", "status": "passed", "duration": 3.2, "error": ""}]
  }
  ```
- 可在 `config.yaml` 中 `monitor.realtime_print` 控制是否实时打印。

### 失败截图机制

`conftest.py` 的 `pytest_runtest_makereport`（hookwrapper）在 call/setup/teardown 失败时自动：
1. 调用 `u2.screenshot()` 保存到 `reports/screenshots/`
2. `allure.attach` 到当前用例
3. 报告中可直接查看失败现场截图

---

## 10. 常见问题 FAQ

**Q1: 收集不到 YAML 用例？**
确保用例文件在 `testcases/yaml_cases/`，且 `case_name` 以 `test_` 开头；运行器文件名必须匹配 pytest 的 `test_*.py`（已命名为 `test_yaml_runner.py`）。

**Q2: YAML 报 `expected ',' or '}'` 解析错误？**
`{ }` 内部含 `${var}` 的值需加引号：`text: "${var}"`。

**Q3: `未检测到 allure 命令行工具`？**
安装 Allure CLI：`brew install allure`（macOS）或下载 release 包加入 PATH。

**Q4: 连接设备失败？**
- `adb devices` 确认设备在线
- 真机开启 USB 调试并允许电脑调试
- 首次运行执行 `python -m uiautomator2 init` 初始化 atx-agent
- WiFi 连接需确保 PC 与设备同网段

**Q5: 如何切换被测 APP？**
改 `config/config.yaml` 的 `app.package_name`；若用 Page Object，同步更新对应 PO 的元素定位值。

**Q6: 如何只跑某优先级而不影响 CI 全量？**
`python run.py --priority P0,P1` 或 `python -m pytest -m "P0 or P1"`。

**Q7: 日志和报告在哪？**
- 日志：`logs/run_YYYY-MM-DD.log`（按天+按10MB轮转，保留7天）
- 报告：`reports/allure-html/index.html`
- 汇总：`reports/summary.json`
- 截图：`reports/screenshots/`

**Q8: 如何扩展新关键字？**
在 `keywords/app_keywords.py` 新增 `_kw_xxx` 方法并注册到 `_handlers()` 字典即可，YAML 立即可用。

---

## 示例用例一览

| 文件 | 类型 | 演示要点 |
|------|------|----------|
| `testcases/test_home.py` | pytest 脚本 | YAML 数据分离 + 参数化 + smoke/P0 标记 + PO |
| `testcases/test_login.py` | pytest 脚本 | 内联数据 + Excel 数据双源 + skipif + P1 |
| `testcases/yaml_cases/test_search.yaml` | YAML 用例 | 关键字编排 + `${var}` 模板 + 断言 + 截图 |
| `testcases/yaml_cases/test_login.yaml` | YAML 用例 | 参数化多账号 + 正反向 + 多种断言 |
| `data/search_data.yaml` | 数据 | YAML 参数化数据集 |
| `data/login_data.xlsx` | 数据 | Excel 参数化数据集 |

---

## 依赖版本

见 [requirements.txt](requirements.txt)。核心：uiautomator2≥3.2 / pytest≥7.4 / allure-pytest≥2.13 / PyYAML≥6.0 / openpyxl≥3.1 / loguru≥0.7。

---

扩展建议通过 `keywords` 与 `pages` 两层加法式扩展，保持核心稳定。
