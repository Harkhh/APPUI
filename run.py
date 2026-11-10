"""测试运行入口

功能：
- 命令行参数：用例路径 / 优先级 / mark 过滤 / 关键字 / 重试 / 是否仅 YAML
- 调用 pytest 执行
- 执行后生成 Allure HTML 报告（中文环境由 allure_config.yaml 定制）
- 同步生成 environment/categories/executor 元数据

常用：
    python run.py                         # 跑全部
    python run.py --priority P0           # 仅 P0
    python run.py -m smoke                # 仅冒烟
    python run.py -k search               # 按名匹配
    python run.py --yaml-only             # 仅跑 YAML 用例
    python run.py --reruns 2              # 失败重试 2 次
    python run.py --no-report             # 不生成 HTML 报告
"""
import argparse
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 把项目根加入 sys.path，保证 `from utils...` 可用
sys.path.insert(0, BASE_DIR)

from utils.allure_utils import prepare_allure, generate_environment_properties, load_allure_config
from utils.log_utils import get_logger
from utils.yaml_utils import load_yaml

logger = get_logger()


def parse_args():
    p = argparse.ArgumentParser(description="APP UI 自动化测试运行入口")
    p.add_argument("paths", nargs="*", default=["testcases"], help="用例路径，默认 testcases")
    p.add_argument("--priority", default="", help="按优先级过滤: P0,P1,...")
    p.add_argument("-m", "--mark", default="", help="pytest -m 表达式，如 smoke")
    p.add_argument("-k", "--keyword", default="", help="pytest -k 关键字匹配")
    p.add_argument("--reruns", type=int, default=0, help="失败重试次数")
    p.add_argument("--yaml-only", action="store_true", help="仅运行 YAML 用例")
    p.add_argument("--no-report", action="store_true", help="不自动生成 Allure HTML 报告")
    p.add_argument("--allure-serve", action="store_true", help="直接 allure serve 打开报告")
    p.add_argument("--env", default="", help="环境标识，写入报告 environment")
    return p.parse_args()


def build_pytest_args(args) -> list:
    cmd = []
    # 路径
    if args.yaml_only:
        cmd.append(os.path.join("testcases", "yaml_test_runner.py"))
    else:
        cmd.extend(args.paths)

    # mark / keyword
    if args.mark:
        cmd += ["-m", args.mark]
    if args.keyword:
        cmd += ["-k", args.keyword]
    if args.reruns:
        cmd += ["--reruns", str(args.reruns), "--reruns-delay", "2"]
    if args.priority:
        cmd += ["--priority", args.priority]

    # allure 结果目录（与日志分离）
    cmd += ["--alluredir", os.path.join("reports", "allure-results"), "--clean-alluredir"]
    return cmd


def run_pytest(cmd: list) -> int:
    logger.info(f"执行 pytest: {' '.join(cmd)}")
    # 用 -m pytest 调用，保证插件加载完整
    full = [sys.executable, "-m", "pytest"] + cmd
    return subprocess.call(full, cwd=BASE_DIR)


def build_allure_report(env_tag: str = "") -> int:
    """生成 Allure HTML 报告。"""
    results = os.path.join(BASE_DIR, "reports", "allure-results")
    html = os.path.join(BASE_DIR, "reports", "allure-html")

    # 补充环境变量（运行后才知道的设备/包名信息）
    try:
        cfg = load_yaml(os.path.join(BASE_DIR, "config", "config.yaml"))
        env_extra = {
            "APP 包名": cfg.get("app", {}).get("package_name", ""),
            "设备连接": cfg.get("device", {}).get("connect_type", "usb"),
        }
        if env_tag:
            env_extra["运行环境"] = env_tag
        generate_environment_properties(results, env_extra)
    except Exception as e:
        logger.warning(f"补充环境信息失败: {e}")

    # 调用 allure 命令行
    if not _has_allure_cli():
        logger.error("未检测到 allure 命令行工具，跳过 HTML 生成。请安装: brew install allure")
        return 1
    cmd = ["allure", "generate", results, "-o", html, "--clean"]
    logger.info(f"生成 Allure 报告: {' '.join(cmd)}")
    return subprocess.call(cmd)


def _has_allure_cli() -> bool:
    from shutil import which
    return which("allure") is not None


def main():
    args = parse_args()

    # 预生成 Allure 元数据（中文 environment/categories）
    prepare_allure()

    cmd = build_pytest_args(args)
    code = run_pytest(cmd)

    if not args.no_report:
        if args.allure_serve:
            results = os.path.join(BASE_DIR, "reports", "allure-results")
            logger.info("启动 allure serve...")
            subprocess.call(["allure", "serve", results])
        else:
            build_allure_report(args.env)

    logger.info(f"运行结束，退出码 {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
