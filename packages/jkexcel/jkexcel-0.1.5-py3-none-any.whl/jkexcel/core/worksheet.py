from typing import List, Optional, Union, Dict, Any
import win32com.client

from jkexcel.core.range import Range
from jkexcel.models.config import SheetVisibility, RangeStyle
from jkexcel.models.exceptions import WorksheetNotFoundError, RangeError


class Worksheet:
    """Excel 工作表封装类"""

    def __init__(self, com_worksheet):
        """
        初始化 Worksheet

        Args:
            com_worksheet: COM Worksheet 对象
        """
        if com_worksheet is None:
            raise WorksheetNotFoundError("COM Worksheet 对象不能为 None")
        self._worksheet = com_worksheet

    def __repr__(self) -> str:
        return f"<Worksheet '{self.name}'>"

    @property
    def com_object(self):
        """获取底层 COM 对象"""
        return self._worksheet

    @property
    def name(self) -> str:
        """获取或设置工作表名称"""
        try:
            return self._worksheet.Name
        except Exception as e:
            raise WorksheetNotFoundError(f"获取名称失败: {e}")

    @name.setter
    def name(self, name: str):
        """设置工作表名称"""
        try:
            self._worksheet.Name = name
        except Exception as e:
            raise WorksheetNotFoundError(f"设置名称失败: {e}")

    @property
    def index(self) -> int:
        """获取工作表索引"""
        try:
            return self._worksheet.Index
        except Exception as e:
            raise WorksheetNotFoundError(f"获取索引失败: {e}")

    @property
    def visible(self) -> bool:
        """获取或设置可见性"""
        try:
            return self._worksheet.Visible == SheetVisibility.VISIBLE.value
        except Exception as e:
            raise WorksheetNotFoundError(f"获取可见性失败: {e}")

    @visible.setter
    def visible(self, visible: bool):
        """设置可见性"""
        try:
            visibility = SheetVisibility.VISIBLE.value if visible else SheetVisibility.HIDDEN.value
            self._worksheet.Visible = visibility
        except Exception as e:
            raise WorksheetNotFoundError(f"设置可见性失败: {e}")

    def set_visibility(self, visibility: SheetVisibility):
        """
        设置可见性

        Args:
            visibility: 可见性枚举
        """
        try:
            self._worksheet.Visible = visibility.value
        except Exception as e:
            raise WorksheetNotFoundError(f"设置可见性失败: {e}")

    @property
    def used_range(self) -> Range:
        """获取使用的范围"""
        try:
            return Range(self._worksheet.UsedRange)
        except Exception as e:
            raise WorksheetNotFoundError(f"获取使用范围失败: {e}")

    def get_range(self, address: str) -> Range:
        """
        通过地址获取范围

        Args:
            address: 范围地址，如 "A1", "A1:B10"

        Returns:
            Range 对象
        """
        try:
            return Range(self._worksheet.Range(address))
        except Exception as e:
            raise RangeError(f"获取范围失败: {e}")

    def get_cell(self, row: int, column: int) -> Range:
        """
        通过行列获取单元格

        Args:
            row: 行号（从1开始）
            column: 列号（从1开始）

        Returns:
            Range 对象
        """
        try:
            return Range(self._worksheet.Cells(row, column))
        except Exception as e:
            raise RangeError(f"获取单元格失败: {e}")

    def get_cells(self, start_row: int, start_col: int,
                  end_row: int = None, end_col: int = None) -> Range:
        """
        获取单元格范围

        Args:
            start_row: 起始行
            start_col: 起始列
            end_row: 结束行（None 表示只取一行）
            end_col: 结束列（None 表示只取一列）

        Returns:
            Range 对象
        """
        try:
            if end_row is None:
                end_row = start_row
            if end_col is None:
                end_col = start_col

            return Range(self._worksheet.Range(
                self._worksheet.Cells(start_row, start_col),
                self._worksheet.Cells(end_row, end_col)
            ))
        except Exception as e:
            raise RangeError(f"获取单元格范围失败: {e}")

    def activate(self):
        """激活工作表"""
        try:
            self._worksheet.Activate()
        except Exception as e:
            raise WorksheetNotFoundError(f"激活工作表失败: {e}")

    def select(self):
        """选择工作表"""
        try:
            self._worksheet.Select()
        except Exception as e:
            raise WorksheetNotFoundError(f"选择工作表失败: {e}")

    def delete(self):
        """删除工作表"""
        try:
            self._worksheet.Delete()
        except Exception as e:
            raise WorksheetNotFoundError(f"删除工作表失败: {e}")

    def copy(self, before: Optional['Worksheet'] = None,
             after: Optional['Worksheet'] = None) -> 'Worksheet':
        """
        复制工作表

        Args:
            before: 复制到指定工作表之前
            after: 复制到指定工作表之后

        Returns:
            新的 Worksheet 对象
        """
        try:
            if before:
                new_sheet = self._worksheet.Copy(Before=before.com_object)
            elif after:
                new_sheet = self._worksheet.Copy(After=after.com_object)
            else:
                new_sheet = self._worksheet.Copy()

            return Worksheet(new_sheet)
        except Exception as e:
            raise WorksheetNotFoundError(f"复制工作表失败: {e}")

    def move(self, before: Optional['Worksheet'] = None,
             after: Optional['Worksheet'] = None):
        """
        移动工作表

        Args:
            before: 移动到指定工作表之前
            after: 移动到指定工作表之后
        """
        try:
            if before:
                self._worksheet.Move(Before=before.com_object)
            elif after:
                self._worksheet.Move(After=after.com_object)
            else:
                self._worksheet.Move()
        except Exception as e:
            raise WorksheetNotFoundError(f"移动工作表失败: {e}")

    def protect(self, password: str = "",
                allow_formatting_cells: bool = True,
                allow_formatting_columns: bool = True,
                allow_formatting_rows: bool = True,
                allow_inserting_columns: bool = True,
                allow_inserting_rows: bool = True,
                allow_inserting_hyperlinks: bool = True,
                allow_deleting_columns: bool = True,
                allow_deleting_rows: bool = True,
                allow_sorting: bool = True,
                allow_filtering: bool = True,
                allow_using_pivot_tables: bool = True):
        """
        保护工作表

        Args:
            password: 密码
            allow_xxx: 允许的操作
        """
        try:
            self._worksheet.Protect(
                Password=password,
                DrawingObjects=True,
                Contents=True,
                Scenarios=True,
                AllowFormattingCells=allow_formatting_cells,
                AllowFormattingColumns=allow_formatting_columns,
                AllowFormattingRows=allow_formatting_rows,
                AllowInsertingColumns=allow_inserting_columns,
                AllowInsertingRows=allow_inserting_rows,
                AllowInsertingHyperlinks=allow_inserting_hyperlinks,
                AllowDeletingColumns=allow_deleting_columns,
                AllowDeletingRows=allow_deleting_rows,
                AllowSorting=allow_sorting,
                AllowFiltering=allow_filtering,
                AllowUsingPivotTables=allow_using_pivot_tables
            )
        except Exception as e:
            raise WorksheetNotFoundError(f"保护工作表失败: {e}")

    def unprotect(self, password: str = ""):
        """
        取消保护

        Args:
            password: 密码
        """
        try:
            self._worksheet.Unprotect(Password=password)
        except Exception as e:
            raise WorksheetNotFoundError(f"取消保护失败: {e}")

    def auto_fit_columns(self, start_col: int = 1, end_col: int = None):
        """
        自动调整列宽

        Args:
            start_col: 起始列
            end_col: 结束列
        """
        try:
            if end_col is None:
                col_range = self._worksheet.Columns(start_col)
            else:
                col_range = self._worksheet.Range(
                    self._worksheet.Cells(1, start_col),
                    self._worksheet.Cells(1, end_col)
                ).EntireColumn

            col_range.AutoFit()
        except Exception as e:
            raise WorksheetNotFoundError(f"自动调整列宽失败: {e}")

    def auto_fit_rows(self, start_row: int = 1, end_row: int = None):
        """
        自动调整行高

        Args:
            start_row: 起始行
            end_row: 结束行
        """
        try:
            if end_row is None:
                row_range = self._worksheet.Rows(start_row)
            else:
                row_range = self._worksheet.Range(
                    self._worksheet.Cells(start_row, 1),
                    self._worksheet.Cells(end_row, 1)
                ).EntireRow

            row_range.AutoFit()
        except Exception as e:
            raise WorksheetNotFoundError(f"自动调整行高失败: {e}")

    def insert_row(self, row: int, count: int = 1):
        """
        插入行

        Args:
            row: 插入位置
            count: 插入数量
        """
        try:
            self.get_cells(row, 1, row + count - 1, 1).com_object.EntireRow.Insert()
        except Exception as e:
            raise WorksheetNotFoundError(f"插入行失败: {e}")

    def insert_column(self, column: int, count: int = 1):
        """
        插入列

        Args:
            column: 插入位置
            count: 插入数量
        """
        try:
            col_letter = self._column_to_letter(column)
            end_col_letter = self._column_to_letter(column + count - 1)
            self._worksheet.Range(f"{col_letter}:{end_col_letter}").Insert()
        except Exception as e:
            raise WorksheetNotFoundError(f"插入列失败: {e}")

    def delete_row(self, row: int, count: int = 1):
        """
        删除行

        Args:
            row: 删除起始行
            count: 删除数量
        """
        try:
            self.get_cells(row, 1, row + count - 1, 1).com_object.EntireRow.Delete()
        except Exception as e:
            raise WorksheetNotFoundError(f"删除行失败: {e}")

    def delete_column(self, column: int, count: int = 1):
        """
        删除列

        Args:
            column: 删除起始列
            count: 删除数量
        """
        try:
            col_letter = self._column_to_letter(column)
            end_col_letter = self._column_to_letter(column + count - 1)
            self._worksheet.Range(f"{col_letter}:{end_col_letter}").Delete()
        except Exception as e:
            raise WorksheetNotFoundError(f"删除列失败: {e}")

    def write_data(self, data: List[List[Any]], start_cell: str = "A1",
                   headers: List[str] = None, style: RangeStyle = None):
        """
        写入数据

        Args:
            data: 二维数据列表
            start_cell: 起始单元格
            headers: 表头列表
            style: 样式配置
        """
        try:
            # 写入表头
            if headers:
                header_range = self.get_range(start_cell).resize(
                    rows=1,
                    cols=len(headers)
                )
                header_range.value = [headers]
                if style:
                    header_range.apply_style(style)

                # 计算数据起始位置
                start_row = self.get_range(start_cell).row + 1
                start_col = self.get_range(start_cell).column
                data_range = self.get_cells(start_row, start_col)
            else:
                data_range = self.get_range(start_cell)

            # 写入数据
            if data:
                data_range.resize(rows=len(data), cols=len(data[0])).value = data

        except Exception as e:
            raise WorksheetNotFoundError(f"写入数据失败: {e}")

    def read_data(self, start_cell: str = "A1",
                  has_headers: bool = False) -> Dict[str, Any]:
        """
        读取数据

        Args:
            start_cell: 起始单元格
            has_headers: 是否有表头

        Returns:
            字典，包含 headers 和 data
        """
        try:
            data_range = self.get_range(start_cell)

            if not data_range:
                return {"headers": [], "data": []}

            values = data_range.get_values()

            if has_headers and values:
                headers = values[0]
                data = values[1:]
                return {"headers": headers, "data": data}
            else:
                return {"headers": [], "data": values}

        except Exception as e:
            raise WorksheetNotFoundError(f"读取数据失败: {e}")

    def add_table(self, range_address: str, name: str = None,
                  has_headers: bool = True):
        """
        添加表格

        Args:
            range_address: 范围地址
            name: 表格名称
            has_headers: 是否有表头
        """
        try:
            table_range = self.get_range(range_address)

            # 创建表
            table = self._worksheet.ListObjects.Add(
                SourceType=1,  # xlSrcRange
                Source=table_range.com_object,
                XlListObjectHasHeaders=1 if has_headers else 2
            )

            if name:
                table.Name = name

            return table
        except Exception as e:
            raise WorksheetNotFoundError(f"添加表格失败: {e}")

    def _column_to_letter(self, column: int) -> str:
        """列号转字母"""
        result = ""
        while column > 0:
            column, remainder = divmod(column - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def _letter_to_column(self, letter: str) -> int:
        """字母转列号"""
        result = 0
        for char in letter.upper():
            result = result * 26 + (ord(char) - 64)
        return result

    # Range 的便捷方法代理
    def current_region(self, start_cell: str = "A1") -> Range:
        """获取当前区域"""
        return self.get_range(start_cell).current_region

    def find(self, what: str, look_in: int = -4163) -> Optional[Range]:
        """查找内容"""
        return self.used_range.find(what, look_in)

    def find_all(self, what: str, look_in: int = -4163) -> List[Range]:
        """查找所有匹配项"""
        return self.used_range.find_all(what, look_in)