from typing import Any, List, Tuple, Optional, Union
import win32com.client

from jkexcel.models.config import RangeStyle
from jkexcel.models.exceptions import RangeError


class Range:
    """Excel 范围封装类"""

    def __init__(self, com_range):
        """
        初始化 Range

        Args:
            com_range: COM Range 对象
        """
        if com_range is None:
            raise RangeError("COM Range 对象不能为 None")
        self._range = com_range

    def __repr__(self) -> str:
        return f"<Range '{self.address}'>"

    @property
    def com_object(self):
        """获取底层 COM 对象"""
        return self._range

    @property
    def address(self) -> str:
        """获取范围地址（如 A1:B10）"""
        try:
            return self._range.Address.replace('$', '')
        except Exception as e:
            raise RangeError(f"获取地址失败: {e}")

    @property
    def value(self) -> Any:
        """获取或设置范围的值"""
        try:
            return self._range.Value
        except Exception as e:
            raise RangeError(f"获取值失败: {e}")

    @value.setter
    def value(self, value: Any):
        """设置范围的值"""
        try:
            self._range.Value = value
        except Exception as e:
            raise RangeError(f"设置值失败: {e}")

    @property
    def formula(self) -> str:
        """获取或设置公式"""
        try:
            return self._range.Formula
        except Exception as e:
            raise RangeError(f"获取公式失败: {e}")

    @formula.setter
    def formula(self, formula: str):
        """设置公式"""
        try:
            self._range.Formula = formula
        except Exception as e:
            raise RangeError(f"设置公式失败: {e}")

    @property
    def text(self) -> str:
        """获取文本"""
        try:
            return self._range.Text
        except Exception as e:
            raise RangeError(f"获取文本失败: {e}")

    @property
    def row(self) -> int:
        """获取起始行号"""
        try:
            return self._range.Row
        except Exception as e:
            raise RangeError(f"获取行号失败: {e}")

    @property
    def column(self) -> int:
        """获取起始列号"""
        try:
            return self._range.Column
        except Exception as e:
            raise RangeError(f"获取列号失败: {e}")

    @property
    def row_height(self) -> float:
        """获取或设置行高"""
        try:
            return self._range.RowHeight
        except Exception as e:
            raise RangeError(f"获取行高失败: {e}")

    @row_height.setter
    def row_height(self, height: float):
        """设置行高"""
        try:
            self._range.RowHeight = height
        except Exception as e:
            raise RangeError(f"设置行高失败: {e}")

    @property
    def column_width(self) -> float:
        """获取或设置列宽"""
        try:
            return self._range.ColumnWidth
        except Exception as e:
            raise RangeError(f"获取列宽失败: {e}")

    @column_width.setter
    def column_width(self, width: float):
        """设置列宽"""
        try:
            self._range.ColumnWidth = width
        except Exception as e:
            raise RangeError(f"设置列宽失败: {e}")

    def get_values(self) -> List[List[Any]]:
        """
        获取范围的值（二维列表）

        Returns:
            二维列表的值
        """
        try:
            values = self._range.Value
            if values is None:
                return []

            # 处理单个单元格
            if not isinstance(values, (list, tuple)):
                return [[values]]

            # 处理单行或单列
            if isinstance(values[0], (list, tuple)):
                return [list(row) for row in values]
            else:
                return [list(values)]

        except Exception as e:
            raise RangeError(f"获取值失败: {e}")

    def set_values(self, values: Union[List[List[Any]], List[Any], Any]):
        """
        设置范围的值

        Args:
            values: 值，可以是二维列表、一维列表或单个值
        """
        try:
            self._range.Value = values
        except Exception as e:
            raise RangeError(f"设置值失败: {e}")

    def clear(self, clear_format: bool = False):
        """
        清除范围内容

        Args:
            clear_format: 是否清除格式
        """
        try:
            if clear_format:
                self._range.Clear()
            else:
                self._range.ClearContents()
        except Exception as e:
            raise RangeError(f"清除失败: {e}")

    def copy(self, destination: Optional['Range'] = None):
        """
        复制范围

        Args:
            destination: 目标范围，None 表示复制到剪贴板
        """
        try:
            self._range.Copy(Destination=destination.com_object if destination else None)
        except Exception as e:
            raise RangeError(f"复制失败: {e}")

    def paste(self, paste_type: int = -4104):
        """
        粘贴（需要在 copy 之后调用）

        Args:
            paste_type: 粘贴类型
                -4104: 全部
                -4122: 值
                -4163: 格式
        """
        try:
            self._range.PasteSpecial(Paste=paste_type)
        except Exception as e:
            raise RangeError(f"粘贴失败: {e}")

    def autofit(self, columns: bool = True, rows: bool = False):
        """
        自动调整大小

        Args:
            columns: 是否自动调整列宽
            rows: 是否自动调整行高
        """
        try:
            if columns:
                self._range.Columns.AutoFit()
            if rows:
                self._range.Rows.AutoFit()
        except Exception as e:
            raise RangeError(f"自动调整失败: {e}")

    def merge(self, across: bool = False):
        """
        合并单元格

        Args:
            across: 是否跨行合并
        """
        try:
            self._range.Merge(Across=across)
        except Exception as e:
            raise RangeError(f"合并单元格失败: {e}")

    def unmerge(self):
        """取消合并"""
        try:
            self._range.UnMerge()
        except Exception as e:
            raise RangeError(f"取消合并失败: {e}")

    def apply_style(self, style: RangeStyle):
        """
        应用样式

        Args:
            style: 样式配置
        """
        try:
            if style.font_name:
                self._range.Font.Name = style.font_name
            if style.font_size:
                self._range.Font.Size = style.font_size
            if style.font_bold is not None:
                self._range.Font.Bold = style.font_bold
            if style.font_italic is not None:
                self._range.Font.Italic = style.font_italic
            if style.font_color is not None:
                self._range.Font.Color = style.font_color
            if style.fill_color is not None:
                self._range.Interior.Color = style.fill_color
            if style.horizontal_alignment is not None:
                self._range.HorizontalAlignment = style.horizontal_alignment
            if style.vertical_alignment is not None:
                self._range.VerticalAlignment = style.vertical_alignment
            if style.number_format:
                self._range.NumberFormat = style.number_format
            if style.wrap_text is not None:
                self._range.WrapText = style.wrap_text
        except Exception as e:
            raise RangeError(f"应用样式失败: {e}")

    def find(self, what: str, look_in: int = -4163) -> Optional['Range']:
        """
        查找内容

        Args:
            what: 要查找的内容
            look_in: 查找范围
                -4163: 公式
                -4123: 值
                -4144: 批注

        Returns:
            找到的范围或 None
        """
        try:
            found = self._range.Find(
                What=what,
                LookIn=look_in
            )
            if found:
                return Range(found)
            return None
        except Exception as e:
            raise RangeError(f"查找失败: {e}")

    def find_all(self, what: str, look_in: int = -4163) -> List['Range']:
        """
        查找所有匹配项

        Args:
            what: 要查找的内容
            look_in: 查找范围

        Returns:
            找到的范围列表
        """
        try:
            first = self._range.Find(
                What=what,
                LookIn=look_in
            )
            if not first:
                return []

            found_ranges = [Range(first)]
            current = first

            while True:
                current = self._range.FindNext(current)
                if not current or current.Address == first.Address:
                    break
                found_ranges.append(Range(current))

            return found_ranges
        except Exception as e:
            raise RangeError(f"查找所有失败: {e}")

    def replace(self, what: str, replacement: str, look_in: int = -4163):
        """
        替换内容

        Args:
            what: 要查找的内容
            replacement: 替换为的内容
            look_in: 查找范围
        """
        try:
            self._range.Replace(
                What=what,
                Replacement=replacement,
                LookAt=1,  # 完全匹配
                LookIn=look_in
            )
        except Exception as e:
            raise RangeError(f"替换失败: {e}")

    def sort(self, key_range: 'Range',
             order: int = 1,  # 1=升序, 2=降序
             header: int = 1):  # 1=有标题, 2=无标题
        """
        排序

        Args:
            key_range: 排序关键字范围
            order: 排序顺序
            header: 是否有标题
        """
        try:
            self._range.Sort(
                Key1=key_range.com_object,
                Order1=order,
                Header=header
            )
        except Exception as e:
            raise RangeError(f"排序失败: {e}")

    def to_list(self) -> List[List[Any]]:
        """转换为二维列表（别名）"""
        return self.get_values()

    def to_flat_list(self) -> List[Any]:
        """转换为一维列表"""
        values = self.get_values()
        flat_list = []
        for row in values:
            if isinstance(row, list):
                flat_list.extend(row)
            else:
                flat_list.append(row)
        return flat_list