import os
import re
import json
from typing import Union, List, Dict, Any, Tuple
from pathlib import Path


def excel_column_to_number(column: str) -> int:
    """
    Excel 列字母转数字

    Args:
        column: 列字母（如 "A", "AB"）

    Returns:
        列号（从1开始）
    """
    result = 0
    for char in column.upper():
        if 'A' <= char <= 'Z':
            result = result * 26 + (ord(char) - 64)
    return result


def number_to_excel_column(number: int) -> str:
    """
    数字转 Excel 列字母

    Args:
        number: 列号（从1开始）

    Returns:
        列字母
    """
    result = ""
    while number > 0:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def cell_address_to_indices(address: str) -> Tuple[int, int]:
    """
    单元格地址转行列索引

    Args:
        address: 单元格地址（如 "A1", "AB123"）

    Returns:
        (行号, 列号)
    """
    match = re.match(r'([A-Z]+)(\d+)$', address.upper())
    if not match:
        raise ValueError(f"无效的单元格地址: {address}")

    col_letters, row_str = match.groups()
    col_num = excel_column_to_number(col_letters)
    row_num = int(row_str)

    return row_num, col_num


def indices_to_cell_address(row: int, col: int) -> str:
    """
    行列索引转单元格地址

    Args:
        row: 行号
        col: 列号

    Returns:
        单元格地址
    """
    col_letter = number_to_excel_column(col)
    return f"{col_letter}{row}"


def range_to_indices(range_address: str) -> Tuple[int, int, int, int]:
    """
    范围地址转索引

    Args:
        range_address: 范围地址（如 "A1:B10"）

    Returns:
        (起始行, 起始列, 结束行, 结束列)
    """
    if ':' in range_address:
        start_addr, end_addr = range_address.split(':')
        start_row, start_col = cell_address_to_indices(start_addr)
        end_row, end_col = cell_address_to_indices(end_addr)
    else:
        start_row, start_col = cell_address_to_indices(range_address)
        end_row, end_col = start_row, start_col

    return start_row, start_col, end_row, end_col


def ensure_dir_exists(file_path: str) -> str:
    """
    确保目录存在

    Args:
        file_path: 文件路径

    Returns:
        绝对路径
    """
    path = Path(file_path).absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    获取文件信息

    Args:
        file_path: 文件路径

    Returns:
        文件信息字典
    """
    path = Path(file_path)
    return {
        'name': path.name,
        'stem': path.stem,
        'suffix': path.suffix,
        'parent': str(path.parent),
        'absolute': str(path.absolute()),
        'exists': path.exists(),
        'size': path.stat().st_size if path.exists() else 0,
        'modified': path.stat().st_mtime if path.exists() else 0,
    }


def rgb_to_excel_color(r: int, g: int, b: int) -> int:
    """
    RGB 转 Excel 颜色值

    Args:
        r: 红色 (0-255)
        g: 绿色 (0-255)
        b: 蓝色 (0-255)

    Returns:
        Excel 颜色值
    """
    return b * 65536 + g * 256 + r


def excel_color_to_rgb(color: int) -> Tuple[int, int, int]:
    """
    Excel 颜色值转 RGB

    Args:
        color: Excel 颜色值

    Returns:
        (R, G, B)
    """
    r = color & 0xFF
    g = (color >> 8) & 0xFF
    b = (color >> 16) & 0xFF
    return r, g, b