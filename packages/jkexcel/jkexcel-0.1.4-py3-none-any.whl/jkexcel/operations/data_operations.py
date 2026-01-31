from typing import List, Dict, Any, Optional, Union
import pandas as pd

from jkexcel.core.range import Range
from jkexcel.core.worksheet import Worksheet
from jkexcel.utils.validators import validate_range_address


class DataOperations:
    """数据操作类"""

    def __init__(self, worksheet: Worksheet):
        """
        初始化

        Args:
            worksheet: Worksheet 对象
        """
        self.ws = worksheet

    def read_to_dataframe(self,
                          start_cell: str = "A1",
                          has_headers: bool = True) -> pd.DataFrame:
        """
        读取为 pandas DataFrame

        Args:
            start_cell: 起始单元格
            has_headers: 是否有表头

        Returns:
            DataFrame
        """
        validate_range_address(start_cell)

        data = self.ws.read_data(start_cell=start_cell, has_headers=has_headers)

        if has_headers and data['headers']:
            return pd.DataFrame(data['data'], columns=data['headers'])
        else:
            return pd.DataFrame(data['data'])

    def write_from_dataframe(self,
                             df: pd.DataFrame,
                             start_cell: str = "A1",
                             include_index: bool = False,
                             include_headers: bool = True):
        """
        从 DataFrame 写入

        Args:
            df: DataFrame
            start_cell: 起始单元格
            include_index: 是否包含索引
            include_headers: 是否包含表头
        """
        validate_range_address(start_cell)

        if include_index:
            df = df.reset_index()

        data = df.values.tolist()
        headers = df.columns.tolist() if include_headers else None

        self.ws.write_data(
            data=data,
            start_cell=start_cell,
            headers=headers
        )

    def filter_data(self,
                    criteria_range: str,
                    criteria: Dict[str, Any]) -> List[Range]:
        """
        筛选数据

        Args:
            criteria_range: 条件范围
            criteria: 条件字典 {列: 值}

        Returns:
            匹配的范围列表
        """
        validate_range_address(criteria_range)

        # 实现筛选逻辑
        # ...

    def find_duplicates(self,
                        search_range: str,
                        columns: Optional[List[int]] = None) -> List[Range]:
        """
        查找重复值

        Args:
            search_range: 搜索范围
            columns: 要检查的列索引列表

        Returns:
            重复值的范围列表
        """
        validate_range_address(search_range)

        # 实现查找重复值逻辑
        # ...

    def remove_duplicates(self,
                          search_range: str,
                          columns: Optional[List[int]] = None):
        """
        删除重复值

        Args:
            search_range: 搜索范围
            columns: 要检查的列索引列表
        """
        validate_range_address(search_range)

        # 实现删除重复值逻辑
        # ...