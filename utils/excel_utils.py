"""Excel 测试数据读取工具

支持以 Excel 维护参数化数据：首行为表头，后续每行一条数据，
读出后转为 list[dict]，可直接喂给 @pytest.mark.parametrize。

用法：
    from utils.excel_utils import read_excel
    data = read_excel("data/login_data.xlsx", sheet="登录正向")
"""
from openpyxl import load_workbook


def read_excel(file_path: str, sheet: str = None, include_header: bool = True) -> list:
    """读取 Excel 文件为 list[dict]。

    Args:
        file_path: xlsx 文件路径。
        sheet: 工作表名；None 取活动表。
        include_header: True=首行作为字段名输出 dict；False=输出 list[list]。

    Returns:
        list[dict] 或 list[list]。
    """
    wb = load_workbook(file_path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return []

    if not include_header:
        return [list(r) for r in rows]

    headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(rows[0])]
    result = []
    for row in rows[1:]:
        if all(c is None or str(c).strip() == "" for c in row):
            continue  # 跳过空行
        result.append({headers[i]: row[i] for i in range(min(len(headers), len(row)))})
    return result


def read_excel_cases(file_path: str, sheet: str = None) -> list:
    """读取 Excel 用例（约定：表头含 case_name/steps 等列时按用例行解析）。

    通用便捷方法，等价 read_excel(include_header=True)。
    """
    return read_excel(file_path, sheet=sheet, include_header=True)
