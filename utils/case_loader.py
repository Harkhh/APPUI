"""用例加载器：YAML / Excel -> pytest 测试函数

设计要点：
- 解析 YAML 用例（关键字驱动 steps），动态生成 pytest 可执行函数。
- 支持 marks（smoke / P0 / P1 / P2…）与 severity 自动转 Allure。
- 支持用例内 data 参数化（每行一个 dict，通过 ${var} 模板注入 steps）。
- YAML 用例约定见 README「YAML 用例编写规范」。

生成出的函数会被 testcases/yaml_test_runner.py 注入到模块命名空间，
pytest 收集后即可像普通用例一样执行。
"""
import glob
import os
from typing import List

import allure
import pytest

from utils.log_utils import get_logger
from utils.yaml_utils import load_yaml

logger = get_logger()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 优先级 -> Allure severity
SEVERITY_MAP = {
    "P0": "critical",
    "P1": "normal",
    "P2": "minor",
    "P3": "trivial",
}


class YamlCase:
    """单条 YAML 用例模型。"""

    def __init__(self, case_dict: dict, source_file: str = ""):
        self.name = case_dict.get("case_name") or case_dict.get("name")
        if not self.name:
            raise ValueError(f"用例缺少 case_name: {case_dict}")
        self.feature = case_dict.get("feature", "未分类")
        self.story = case_dict.get("story", "")
        self.severity = case_dict.get("severity", "")
        self.marks = case_dict.get("marks", [])
        self.description = case_dict.get("description", "")
        self.steps = case_dict.get("steps", [])
        self.data = case_dict.get("data", []) or [{}]
        self.source_file = source_file

    def __repr__(self):
        return f"<YamlCase {self.name} steps={len(self.steps)}>"


def load_yaml_cases(yaml_dir: str = None) -> List[YamlCase]:
    """从目录加载所有 YAML 用例。

    Args:
        yaml_dir: 用例目录；None 时取 testcases/yaml_cases/。

    Returns:
        list[YamlCase]
    """
    if yaml_dir is None:
        yaml_dir = os.path.join(BASE_DIR, "testcases", "yaml_cases")
    cases = []
    for fp in sorted(glob.glob(os.path.join(yaml_dir, "*.yaml")) + glob.glob(os.path.join(yaml_dir, "*.yml"))):
        data = load_yaml(fp)
        if not data:
            continue
        if isinstance(data, dict):
            data = [data]
        for case_dict in data:
            try:
                cases.append(YamlCase(case_dict, source_file=fp))
            except ValueError as e:
                logger.error(f"跳过非法用例({fp}): {e}")
    logger.info(f"从 {yaml_dir} 加载到 {len(cases)} 条 YAML 用例")
    return cases


def _resolve_template(text, row: dict):
    """将 ${var} 替换为数据行对应值；非字符串原样返回。"""
    if not isinstance(text, str) or "${" not in text:
        return text
    out = text
    for k, v in row.items():
        out = out.replace("${" + str(k) + "}", str(v))
    return out


def _resolve_step(step: dict, row: dict) -> dict:
    """递归替换 step 内所有字符串中的 ${var}。"""
    resolved = {}
    for k, v in step.items():
        if isinstance(v, str):
            resolved[k] = _resolve_template(v, row)
        elif isinstance(v, dict):
            resolved[k] = _resolve_step(v, row)
        elif isinstance(v, list):
            resolved[k] = [_resolve_template(i, row) if isinstance(i, str) else _resolve_step(i, row) for i in v]
        else:
            resolved[k] = v
    return resolved


def make_test_function(case: YamlCase):
    """根据 YamlCase 动态构造一个 pytest 测试函数。

    依赖 conftest 提供 `d`（u2 设备）与 `request` fixture。
    步骤通过 keywords.AppKeywords.execute_step 执行。
    """
    # 延迟导入避免循环依赖
    from keywords.app_keywords import AppKeywords

    params = case.data if case.data else [{}]
    ids = [row.get("id", f"数据{i + 1}") for i, row in enumerate(params)]

    def test_fn(d, request, row_data, __case=case):
        # Allure 分层标记
        with allure.step(f"用例: {__case.name}"):
            if __case.description:
                allure.dynamic.description(__case.description)
            allure.dynamic.feature(__case.feature)
            if __case.story:
                allure.dynamic.story(__case.story)
            kw = AppKeywords(d, request)
            for idx, step in enumerate(__case.steps, 1):
                step = _resolve_step(step, row_data)
                step_desc = step.get("description") or f"步骤{idx}: {step.get('keyword')}"
                with allure.step(step_desc):
                    kw.execute_step(step)

    # 命名
    test_fn.__name__ = case.name
    test_fn.__doc__ = case.description

    # 组装 marks
    marks = [pytest.mark.parametrize("row_data", params, ids=ids)]
    for m in case.marks:
        try:
            marks.append(getattr(pytest.mark, m))
        except AttributeError:
            logger.warning(f"未知 mark: {m}（用例 {case.name}）")
    if case.severity:
        sev = SEVERITY_MAP.get(case.severity)
        if sev:
            marks.append(allure.severity(sev))
    test_fn.pytestmark = marks
    return test_fn


def register_yaml_cases(module_globals: dict, yaml_dir: str = None) -> List[str]:
    """把 YAML 用例注入到指定模块的命名空间。

    用于 testcases/yaml_test_runner.py：
        from utils.case_loader import register_yaml_cases
        register_yaml_cases(globals())

    Returns:
        已注册的用例函数名列表。
    """
    names = []
    for case in load_yaml_cases(yaml_dir):
        fn = make_test_function(case)
        module_globals[case.name] = fn
        names.append(case.name)
    return names
