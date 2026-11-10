"""YAML 用例自动运行器

本模块不做任何测试逻辑，仅把 testcases/yaml_cases/*.yaml 中的用例
动态注册为 pytest 测试函数。pytest 收集本文件时，模块级代码执行
register_yaml_cases(globals()) 即完成注入。

编写新用例时只需在 yaml_cases/ 下新增 .yaml 文件，无需改本文件。
"""
from utils.case_loader import register_yaml_cases

# 注入 YAML 用例到当前模块命名空间
_REGISTERED = register_yaml_cases(globals())
