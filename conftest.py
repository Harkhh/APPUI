"""pytest 全局配置（conftest）

职责：
1. 注册自定义 mark（smoke / P0 / P1 / P2 / P3 等）
2. 提供 session 级 driver fixture
3. 提供 app fixture（按用例可选重启）
4. 失败自动截图并 attach 到 Allure
5. 接入测试过程监测 Monitor（实时打印 + summary.json）
"""
import os
import time

import pytest

from utils.log_utils import get_logger
from utils.monitor import get_monitor, reset_monitor

logger = get_logger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 自定义标记
CUSTOM_MARKS = [
    "smoke: 冒烟用例",
    "P0: 最高优先级（阻塞级）",
    "P1: 高优先级",
    "P2: 中优先级",
    "P3: 低优先级",
    "regression: 回归用例",
    "flaky: 不稳定用例（失败重试）",
]


# ---------------- mark 注册 ----------------
def pytest_configure(config):
    for mark_desc in CUSTOM_MARKS:
        name = mark_desc.split(":")[0]
        config.addinivalue_line("markers", mark_desc)

    # 重置并启动监测
    cfg_path = os.path.join(BASE_DIR, "config", "config.yaml")
    from utils.yaml_utils import load_yaml
    cfg = load_yaml(cfg_path).get("monitor", {})
    if cfg.get("enable", True):
        summary_file = os.path.join(BASE_DIR, "reports", "summary.json")
        reset_monitor(summary_file=summary_file, realtime_print=cfg.get("realtime_print", True))

    # 预生成 Allure 元数据
    from utils.allure_utils import prepare_allure
    prepare_allure()


def pytest_unconfigure(config):
    # 输出汇总
    from utils.monitor import get_monitor
    try:
        get_monitor().write_summary()
    except Exception as e:
        logger.warning(f"写入 summary 失败: {e}")


# ---------------- fixtures ----------------
@pytest.fixture(scope="session")
def d():
    """uiautomator2 设备（session 级复用）。"""
    from utils.driver_utils import DriverFactory
    device = DriverFactory.connect()
    yield device
    # session 结束无需关闭 atx-agent
    logger.info("设备 session 结束")


@pytest.fixture(scope="function")
def app(d):
    """按配置启动/重启 APP。返回包名。"""
    from utils.driver_utils import DriverFactory
    from utils.yaml_utils import load_yaml
    cfg = load_yaml(os.path.join(BASE_DIR, "config", "config.yaml")).get("app", {})
    pkg = cfg.get("package_name")
    restart = cfg.get("restart_per_case", False)
    keep = cfg.get("keep_data", True)

    if restart:
        DriverFactory.stop_app(d, pkg)
        if not keep:
            DriverFactory.clear_app(d, pkg)
        DriverFactory.launch_app(d, pkg, cfg.get("activity"))
    else:
        # 至少确保 APP 在前台
        try:
            d.app_start(pkg, wait=False)
        except Exception:
            pass
    yield pkg


# ---------------- 失败截图 hook ----------------
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """捕获每阶段结果：失败时截图并 attach 到 Allure；同时喂给 Monitor。"""
    outcome = yield
    report = outcome.get_result()

    # 仅在 call 阶段（实际用例执行）做截图与监测
    if report.when != "call":
        # 失败发生在 setup/teardown 时也截图
        if report.when in ("setup", "teardown") and report.failed:
            _capture_failure_screenshot(item, call, report.when)
        return

    # ----- 监测记录 -----
    monitor = get_monitor()
    status = "passed"
    if report.failed:
        status = "failed"
    elif report.skipped:
        status = "skipped"
    elif hasattr(report, "wasxfail") and report.wasxfail:
        status = "passed"  # xpass

    err = ""
    if report.longrepr:
        try:
            err = str(report.longrepr)[-500:]
        except Exception:
            err = ""
    duration = getattr(report, "duration", 0) or 0
    monitor.on_finish(item.nodeid, status, duration, err)

    # ----- 失败截图 -----
    if report.failed:
        _capture_failure_screenshot(item, call, "call")


def _capture_failure_screenshot(item, call, phase):
    """对失败用例截图。"""
    d = item.funcargs.get("d") if hasattr(item, "funcargs") else None
    if d is None:
        return
    from utils.screenshot_utils import take_screenshot
    name = f"失败_{item.name}_{phase}"
    try:
        take_screenshot(d, name=name, attach=True)
    except Exception as e:
        logger.warning(f"失败截图异常: {e}")


# ---------------- 用例收集后：注入监测 on_start ----------------
def pytest_runtest_setup(item):
    monitor = get_monitor()
    monitor.on_start(item.nodeid)


# ---------------- 命令行扩展：按优先级过滤 ----------------
def pytest_addoption(parser):
    parser.addoption(
        "--priority", action="store", default="", help="按优先级过滤用例: P0/P1/P2/P3，逗号分隔"
    )


def pytest_collection_modifyitems(config, items):
    """支持 --priority 命令行过滤；保留指定优先级用例，其余删除。"""
    priority = config.getoption("--priority")
    if not priority:
        return
    wanted = [p.strip().upper() for p in priority.split(",") if p.strip()]
    selected = []
    for it in items:
        marks = {m.name for m in it.iter_markers()}
        if any(w in marks for w in wanted):
            selected.append(it)
    # 标准 deselected 汇报：通过 items 原地裁剪 + 调用 hook
    deselected = [it for it in items if it not in selected]
    if deselected:
        config.hook.pytest_deselected(items=deselected)
    items[:] = selected
