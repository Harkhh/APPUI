"""Allure 报告定制工具

读取 config/allure_config.yaml，自动生成 Allure 报告所需的元数据：
- environment.properties  顶部环境信息
- categories.json         缺陷分类
- executor.json           执行信息（可选）

这样无需手改 Allure 目录即可定制中文报告页面内容。
"""
import json
import os

from utils.yaml_utils import load_yaml
from utils.log_utils import get_logger

logger = get_logger()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_allure_config() -> dict:
    return load_yaml(os.path.join(BASE_DIR, "config", "allure_config.yaml"))


def generate_environment_properties(allure_results_dir: str = None, env_extra: dict = None) -> str:
    """生成 environment.properties（Allure 顶部环境信息）。

    Args:
        allure_results_dir: allure-results 目录；None 时用 config 默认。
        env_extra: 运行时补充的环境变量（如设备型号、APP 包名）。

    Returns:
        生成的文件路径。
    """
    cfg = load_allure_config()
    env = dict(cfg.get("environment", {}))
    if env_extra:
        env.update(env_extra)

    if allure_results_dir is None:
        allure_results_dir = os.path.join(BASE_DIR, "reports", "allure-results")

    os.makedirs(allure_results_dir, exist_ok=True)
    path = os.path.join(allure_results_dir, "environment.properties")
    with open(path, "w", encoding="utf-8") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")
    logger.info(f"生成 environment.properties: {path}")
    return path


def generate_categories(allure_results_dir: str = None) -> str:
    """生成 categories.json（缺陷分类）。"""
    cfg = load_allure_config()
    categories = cfg.get("categories", [])
    if not categories:
        return ""

    if allure_results_dir is None:
        allure_results_dir = os.path.join(BASE_DIR, "reports", "allure-results")

    os.makedirs(allure_results_dir, exist_ok=True)
    path = os.path.join(allure_results_dir, "categories.json")
    norm = []
    for c in categories:
        item = {"name": c.get("name", ""), "matchedStatuses": c.get("matchedStatuses", [])}
        if c.get("messageRegex"):
            item["messageRegex"] = c["messageRegex"]
        if c.get("traceRegex"):
            item["traceRegex"] = c["traceRegex"]
        norm.append(item)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(norm, f, ensure_ascii=False, indent=2)
    logger.info(f"生成 categories.json: {path}")
    return path


def generate_executor(allure_results_dir: str = None, build_name: str = None, extra: dict = None) -> str:
    """生成 executor.json（执行人/构建信息）。"""
    if allure_results_dir is None:
        allure_results_dir = os.path.join(BASE_DIR, "reports", "allure-results")

    os.makedirs(allure_results_dir, exist_ok=True)
    data = {
        "name": "APP-UI-Auto-Runner",
        "type": "local",
        "buildName": build_name or f"build_{__import__('time').strftime('%Y%m%d_%H%M%S')}",
        "reportName": "APP UI 自动化测试报告",
    }
    if extra:
        data.update(extra)
    path = os.path.join(allure_results_dir, "executor.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"生成 executor.json: {path}")
    return path


def prepare_allure(allure_results_dir: str = None, env_extra: dict = None) -> None:
    """在生成报告前一次性写入所有 Allure 元数据。"""
    generate_environment_properties(allure_results_dir, env_extra)
    generate_categories(allure_results_dir)
    generate_executor(allure_results_dir)


def get_severity_map() -> dict:
    """返回 severity 中英映射，供标记用例时使用。"""
    return load_allure_config().get("severity_map", {})
