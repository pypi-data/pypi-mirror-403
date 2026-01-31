import os
from typing import List, Optional, Iterator, Union

import pythoncom
import win32com.client

from jkexcel.core.workbook import Workbook
from jkexcel.models.enums import Platform, SeparatorFormat, CorruptLoad
from jkexcel.models.exceptions import WorkbookNotFoundError


class Workbooks:
    """Excel 工作簿集合封装类"""

    def __init__(self, com_workbooks, excel_app):
        """
        初始化 Workbooks

        Args:
            com_workbooks: COM Workbooks 对象
            excel_app: ExcelApp 实例
        """
        if com_workbooks is None:
            raise WorkbookNotFoundError("COM Workbooks 对象不能为 None")
        self._workbooks = com_workbooks
        self._excel = excel_app

    def __repr__(self) -> str:
        return f"<Workbooks count={self.count}>"

    def __len__(self) -> int:
        """获取工作簿数量"""
        return self.count

    def __getitem__(self, key: Union[int, str]) -> Workbook:
        """通过索引或名称获取工作簿"""
        return self.get(key)

    def __iter__(self) -> Iterator[Workbook]:
        """迭代工作簿"""
        for i in range(1, self.count + 1):
            yield self.get(i)

    @property
    def com_object(self):
        """获取底层 COM 对象"""
        return self._workbooks

    @property
    def excel_app(self):
        """获取 ExcelApp 实例"""
        return self._excel

    @property
    def count(self) -> int:
        """获取工作簿数量"""
        try:
            return self._workbooks.Count
        except Exception as e:
            raise WorkbookNotFoundError(f"获取工作簿数量失败: {e}")

    @property
    def names(self) -> List[str]:
        """获取所有工作簿名称"""
        return [wb.name for wb in self]

    def get(self, key: Union[int, str]) -> Workbook:
        """
        获取工作簿

        Args:
            key: 索引（从1开始）或名称

        Returns:
            Workbook 对象
        """
        try:
            if isinstance(key, int):
                com_wb = self._workbooks(key)
            else:
                com_wb = self._workbooks(key)
            return Workbook(com_wb, self._excel)
        except Exception as e:
            raise WorkbookNotFoundError(f"获取工作簿失败: {e}")

    def add(self, *args, **kwargs) -> Workbook:
        """
        添加新工作簿 并保存

        Returns:
            Workbook 对象
        """
        try:
            com_wb = self._workbooks.Add()
            wb = Workbook(com_wb, self._excel)
            if 'file_path' in kwargs:
                wb.save_as(*args, **kwargs)
            return wb
        except Exception as e:
            raise WorkbookNotFoundError(f"添加工作簿失败: {e}")

    def open(self, file_path: str,
             update_links: bool = True,
             read_only: bool = False,
             sep_format: Optional[SeparatorFormat] = None,
             password: str = pythoncom.Missing,
             write_res_password: str = pythoncom.Missing,
             ignore_read_only_recommended: bool = True,
             origin: Optional[Platform] = None,
             delimiter: str = pythoncom.Missing,
             editable: bool = pythoncom.Missing,
             notify: bool = pythoncom.Missing,
             converter: int = pythoncom.Missing,
             add_to_mru: bool = False,
             local: bool = False,
             corrupt_load: Optional[CorruptLoad] = CorruptLoad.xlNormalLoad
             ) -> Workbook:
        """
        打开工作簿

        Args:
            file_path: 文件路径
            update_links: 打开工作簿时是否更新外部引用
            read_only: 是否只读
            sep_format: 如果 Microsoft Excel 打开文本文件，则此参数指定分隔符字符。 如果省略此参数，则使用当前分隔符
            password: 包含打开受保护工作簿所需密码的字符串。 如果省略此参数并且工作簿需要密码，则会提示用户输入密码。
            write_res_password: 包含写入写保护的工作簿所需密码的字符串。 如果省略此参数并且工作簿需要密码，则将提示用户输入密码。
            ignore_read_only_recommended: 如果为 True，则不让 Microsoft Excel 显示只读的建议消息（如果该工作簿以建议只读选项保存）。
            origin: 如果文件是文本文件，则此参数表示其来源，这样就可正确映射代码页和回车/换行 (CR/LF)。 可以是以下 `Platform` 常量之一： `xlMacintosh` `xlWindows` 或 `xlMSDOS` 如果省略此参数，则使用当前操作系统。
            delimiter: 如果sep_format设置为 `SeparatorFormat.Custom` 则该表示使用自定义的字符串，注意这里只会选择字符串第一个字符作为分隔符
            editable: 如果文件为 Microsoft Excel 4.0 外接程序，则此参数为 True 时可打开该外接程序以使其成为可见窗口。 如果此参数为 False 或被省略，则以隐藏方式打开外接程序，并且无法设为可见。 此选项不适用于在 Microsoft Excel 5.0 或更高版本中创建的加载项。如果文件是 Excel 模板，则为 True，可打开指定的模板进行编辑。 如果为 False，则可根据指定的模板打开新工作簿
            notify: 当文件不能以可读写模式打开时，如果此参数为 `True`，则可将该文件添加到文件通知列表。 Microsoft Excel 将以只读模式打开该文件并轮询文件通知列表，并在文件可用时向用户发出通知。 如果此参数为 `False` 或省略，则不会请求通知，并且任何打开不可用文件的尝试都将失败。
            converter: 打开文件时要尝试的第一个文件转换器的索引。 首先尝试指定的文件转换器
            add_to_mru: 如果为 `True`，则将该工作簿添加到最近使用的文件列表中。
            local:如果为 True，则以 Microsoft Excel（包括控制面板设置）的语言保存文件。 如果为 False（默认值），则以 Visual Basic for Applications (VBA) 的语言保存文件，其中 Visual Basic for Applications (VBA) 通常为美国英语版本，除非从中运行 Workbooks.Open 的 VBA 项目是旧的已国际化的 XL5/95 VBA 项目
            corrupt_load: 可为以下常量之一：`xlNormalLoad`、`xlRepairFile` 和 `xlExtractData`。 如果未指定值，则默认行为为 `xlNormalLoad`，并且不会在通过 OM 启动时尝试恢复。
        Returns:
            Workbook 对象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            com_wb = self._workbooks.Open(
                Filename=file_path,
                UpdateLinks=0 if update_links else 3,  # 0=更新, 3=不更新
                ReadOnly=read_only,
                Format=sep_format.value if sep_format else pythoncom.Missing,
                Password=password,
                WriteResPassword=write_res_password,
                IgnoreReadOnlyRecommended=ignore_read_only_recommended,
                Origin=origin.value if origin else pythoncom.Missing,
                Delimiter=delimiter,
                Editable=editable,
                Notify=notify,
                Converter=converter,
                AddToMru=add_to_mru,
                Local=local,
                CorruptLoad=corrupt_load.value
            )
            return Workbook(com_wb, self._excel)
        except Exception as e:
            raise WorkbookNotFoundError(f"打开工作簿失败: {e}")

    def close_all(self, save_changes: bool = False):
        """
        关闭所有工作簿

        Args:
            save_changes: 是否保存更改
        """
        for workbook in self:
            try:
                workbook.close(save_changes=save_changes)
            except:
                pass

    def exists(self, name: str) -> bool:
        """
        检查工作簿是否存在

        Args:
            name: 工作簿名称

        Returns:
            bool
        """
        try:
            self._workbooks(name)
            return True
        except:
            return False

    def get_active(self) -> Optional[Workbook]:
        """
        获取活动工作簿

        Returns:
            Workbook 对象或 None
        """
        try:
            com_wb = self._excel.com_object.ActiveWorkbook
            if com_wb:
                return Workbook(com_wb, self._excel)
            return None
        except Exception as e:
            raise WorkbookNotFoundError(f"获取活动工作簿失败: {e}")
