import os
from typing import Any, Union, List, Tuple
from pathlib import Path

from jkexcel.models.exceptions import FileOperationError, InvalidParameterError


def validate_file_exists(file_path: str) -> str:
    """验证文件是否存在"""
    if not os.path.exists(file_path):
        raise FileOperationError(f"文件不存在: {file_path}")

    if not os.path.isfile(file_path):
        raise FileOperationError(f"不是文件: {file_path}")

    return file_path


def validate_directory_exists(dir_path: str) -> str:
    """验证目录是否存在"""
    if not os.path.exists(dir_path):
        raise FileOperationError(f"目录不存在: {dir_path}")

    if not os.path.isdir(dir_path):
        raise FileOperationError(f"不是目录: {dir_path}")

    return dir_path


def validate_excel_file(file_path: str) -> str:
    """验证 Excel 文件"""
    validate_file_exists(file_path)

    ext = Path(file_path).suffix.lower()
    if ext not in ['.xlsx', '.xls', '.xlsm', '.xlsb', '.csv']:
        raise InvalidParameterError(f"不支持的文件格式: {ext}")

    return file_path


def validate_range_address(address: str) -> str:
    """验证范围地址"""
    import re

    # 简单的单元格地址验证
    cell_pattern = r'^[A-Z]{1,3}\d{1,7}$'
    range_pattern = r'^[A-Z]{1,3}\d{1,7}:[A-Z]{1,3}\d{1,7}$'

    if not (re.match(cell_pattern, address.upper()) or
            re.match(range_pattern, address.upper())):
        raise InvalidParameterError(f"无效的范围地址: {address}")

    return address


def validate_row_col(row: int, col: int,
                     min_row: int = 1, max_row: int = 1048576,
                     min_col: int = 1, max_col: int = 16384) -> Tuple[int, int]:
    """验证行列号"""
    if not (min_row <= row <= max_row):
        raise InvalidParameterError(f"行号必须在 {min_row}-{max_row} 之间")

    if not (min_col <= col <= max_col):
        raise InvalidParameterError(f"列号必须在 {min_col}-{max_col} 之间")

    return row, col


def validate_positive_integer(value: Any, name: str = "值") -> int:
    """验证正整数"""
    try:
        num = int(value)
        if num <= 0:
            raise InvalidParameterError(f"{name} 必须是正整数")
        return num
    except (ValueError, TypeError):
        raise InvalidParameterError(f"{name} 必须是整数")


def validate_non_negative_integer(value: Any, name: str = "值") -> int:
    """验证非负整数"""
    try:
        num = int(value)
        if num < 0:
            raise InvalidParameterError(f"{name} 必须是非负整数")
        return num
    except (ValueError, TypeError):
        raise InvalidParameterError(f"{name} 必须是整数")
