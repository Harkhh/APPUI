"""生成示例 Excel 测试数据 data/login_data.xlsx

用法：
    python scripts/gen_login_excel.py

表头：id / username / password / expect_success
每行一条登录用例数据，testcases/test_login.py 通过
utils.excel_utils.read_excel 读取后做参数化。
"""
import os

from openpyxl import Workbook

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(BASE_DIR, "data", "login_data.xlsx")

wb = Workbook()
ws = wb.active
ws.title = "登录用例"

headers = ["id", "username", "password", "expect_success"]
ws.append(headers)

rows = [
    ["正向-admin", "admin", "123456", True],
    ["正向-test", "testuser", "test1234", True],
    ["反向-密码错", "admin", "wrongpwd", False],
    ["反向-空用户", "", "123456", False],
    ["反向-空密码", "admin", "", False],
]
for r in rows:
    ws.append(r)

for i in range(1, len(headers) + 1):
    ws.column_dimensions[chr(64 + i)].width = 18

wb.save(out)
print(f"已生成: {out}")
