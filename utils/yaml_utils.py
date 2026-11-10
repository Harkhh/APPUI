"""YAML 读写工具

提供配置文件与测试数据的统一加载入口，所有 YAML 均由此读取，
保证项目内不散落 PyYAML 直调。
"""
import os
from typing import Any

import yaml


def load_yaml(file_path: str) -> Any:
    """加载 YAML 文件并返回 Python 对象。

    Args:
        file_path: YAML 文件绝对/相对路径。

    Returns:
        解析后的字典/列表；文件不存在时返回空 dict。
    """
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def dump_yaml(data: Any, file_path: str) -> None:
    """将 Python 对象写入 YAML 文件。"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def load_case_data(data_file: str, case_name: str = None) -> list:
    """加载测试数据文件，按用例名取出参数化数据列表。

    约定 data 文件结构：
        case_name:
          - param1: v1
            param2: v2
          - ...

    Args:
        data_file: 数据文件路径。
        case_name: 顶层 key（用例名）；为 None 时返回整个文件内容。

    Returns:
        list[dict]: 参数化数据集；未找到时返回空列表。
    """
    data = load_yaml(data_file)
    if case_name is None:
        return data if isinstance(data, list) else [data] if data else []
    items = data.get(case_name, []) if isinstance(data, dict) else []
    return items if isinstance(items, list) else [items]
