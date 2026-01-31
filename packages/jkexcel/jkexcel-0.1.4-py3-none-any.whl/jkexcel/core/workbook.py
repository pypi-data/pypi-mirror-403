import os
from typing import Optional, List, Dict, Any, Union

import pythoncom

from jkexcel.core.worksheet import Worksheet
from jkexcel.core.worksheets import Worksheets
from jkexcel.models.config import SaveFormat, SaveAsAccessMode, SaveConflictResolution
from jkexcel.models.exceptions import WorkbookNotFoundError


class Workbook:
    """Excel 工作簿封装类"""

    def __init__(self, com_workbook, excel_app):
        """
        初始化 Workbook

        Args:
            com_workbook: COM Workbook 对象
            excel_app: ExcelApp 实例
        """
        if com_workbook is None:
            raise WorkbookNotFoundError("COM Workbook 对象不能为 None")
        self._workbook = com_workbook
        self._excel = excel_app
        self._worksheets = None

    def __repr__(self) -> str:
        return f"<Workbook '{self.name}'>"

    def __enter__(self):
        """上下文管理器进入"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close(save_changes=False)
        return False

    @property
    def com_object(self):
        """获取底层 COM 对象"""
        return self._workbook

    @property
    def excel_app(self):
        """获取 ExcelApp 实例"""
        return self._excel

    @property
    def name(self) -> str:
        """获取工作簿名称"""
        try:
            return self._workbook.Name
        except Exception as e:
            raise WorkbookNotFoundError(f"获取名称失败: {e}")

    @property
    def full_name(self) -> str:
        """获取完整路径"""
        try:
            return self._workbook.FullName
        except Exception as e:
            raise WorkbookNotFoundError(f"获取完整路径失败: {e}")

    @property
    def path(self) -> str:
        """获取路径"""
        try:
            return self._workbook.Path
        except Exception as e:
            raise WorkbookNotFoundError(f"获取路径失败: {e}")

    @property
    def saved(self) -> bool:
        """是否已保存"""
        try:
            return self._workbook.Saved
        except Exception as e:
            raise WorkbookNotFoundError(f"获取保存状态失败: {e}")

    @property
    def read_only(self) -> bool:
        """是否只读"""
        try:
            return self._workbook.ReadOnly
        except Exception as e:
            raise WorkbookNotFoundError(f"获取只读状态失败: {e}")

    @property
    def file_format(self) -> int:
        """获取文件格式"""
        try:
            return self._workbook.FileFormat
        except Exception as e:
            raise WorkbookNotFoundError(f"获取文件格式失败: {e}")

    @property
    def worksheets(self) -> Worksheets:
        """获取工作表集合"""
        if self._worksheets is None:
            self._worksheets = Worksheets(self._workbook.Worksheets)
        return self._worksheets

    @property
    def sheets(self) -> Worksheets:
        """获取所有表（包括图表等）（别名）"""
        return Worksheets(self._workbook.Sheets)

    def activate(self):
        """激活工作簿"""
        try:
            self._workbook.Activate()
        except Exception as e:
            raise WorkbookNotFoundError(f"激活工作簿失败: {e}")

    def save(self):
        """保存工作簿"""
        try:
            self._workbook.Save()
        except Exception as e:
            raise WorkbookNotFoundError(f"保存工作簿失败: {e}")

    def save_as(self, file_path: str, file_format: Optional[SaveFormat] = None,
                password: Optional[str] = pythoncom.Missing,
                write_res_password: Optional[str] = pythoncom.Missing,
                read_only_recommended: Optional[bool] = pythoncom.Missing,
                create_backup: Optional[bool] = pythoncom.Missing,
                access_mode: Optional[SaveAsAccessMode] = None,
                conflict_resolution: Optional[SaveConflictResolution] = None,
                add_to_mru: Optional[bool] = pythoncom.Missing,
                text_code_page: Optional[str] = pythoncom.Missing,
                text_visual_layout: Optional[object] = pythoncom.Missing,
                local: Optional[bool] = pythoncom.Missing):
        """
        另存为
        :param file_path:
        :param file_format:
        :param password:
        :param write_res_password:
        :param read_only_recommended:
        :param create_backup:
        :param access_mode:
        :param conflict_resolution:
        :param add_to_mru:
        :param text_code_page:
        :param text_visual_layout:
        :param local:
        :return:
        """
        if file_format:
            name_without_ext, _ = os.path.splitext(file_path)
            file_name = name_without_ext + file_format.value[1]
        full_path = os.path.abspath(file_path)
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)
        file_name = os.path.normpath(file_path)
        try:
            self._workbook.SaveAs(file_name, file_format.value[0] if file_format else pythoncom.Missing, password,
                                  write_res_password,
                                  read_only_recommended, create_backup,
                                  access_mode.value[0] if access_mode else pythoncom.Missing,
                                  conflict_resolution.value[0] if conflict_resolution else pythoncom.Missing,
                                  add_to_mru,
                                  text_code_page,
                                  text_visual_layout, local)
        except Exception as e:
            raise WorkbookNotFoundError(f"另存为失败: {e}")

    def save_copy_as(self, file_path: str):
        """
        保存副本

        Args:
            file_path: 副本路径
        """
        try:
            self._workbook.SaveCopyAs(file_path)
        except Exception as e:
            raise WorkbookNotFoundError(f"保存副本失败: {e}")

    def close(self, save_changes: bool = True,
              file_path: str = None):
        """
        关闭工作簿

        Args:
            save_changes: 是否保存更改
            file_path: 保存路径（如果为None则使用原路径）
        """
        try:
            if save_changes and file_path:
                self.save_as(file_path)
            elif save_changes:
                self.save()

            self._workbook.Close(SaveChanges=False)
            self._worksheets = None
            
            # 如果是最后一个工作簿，自动退出 Excel
            if self._excel.count == 0:
                self._excel.quit()
        except Exception as e:
            raise WorkbookNotFoundError(f"关闭工作簿失败: {e}")

    def protect(self, password: str = "",
                structure: bool = True,
                windows: bool = False):
        """
        保护工作簿

        Args:
            password: 密码
            structure: 保护结构
            windows: 保护窗口
        """
        try:
            self._workbook.Protect(
                Password=password,
                Structure=structure,
                Windows=windows
            )
        except Exception as e:
            raise WorkbookNotFoundError(f"保护工作簿失败: {e}")

    def unprotect(self, password: str = ""):
        """
        取消保护

        Args:
            password: 密码
        """
        try:
            self._workbook.Unprotect(Password=password)
        except Exception as e:
            raise WorkbookNotFoundError(f"取消保护失败: {e}")

    def refresh_all(self):
        """刷新所有数据"""
        try:
            self._workbook.RefreshAll()
        except Exception as e:
            raise WorkbookNotFoundError(f"刷新数据失败: {e}")

    def calculate(self):
        """计算所有公式"""
        try:
            self._workbook.Application.Calculate()
        except Exception as e:
            raise WorkbookNotFoundError(f"计算失败: {e}")

    def get_active_sheet(self) -> Worksheet:
        """获取活动工作表"""
        try:
            return Worksheet(self._workbook.ActiveSheet)
        except Exception as e:
            raise WorkbookNotFoundError(f"获取活动工作表失败: {e}")

    def add_worksheet(self, before: Union[int, str, Worksheet] = None,
                      after: Union[int, str, Worksheet] = None) -> Worksheet:
        """
        添加新工作表

        Args:
            before: 插入到指定工作表之前
            after: 插入到指定工作表之后

        Returns:
            Worksheet 对象
        """
        return self.worksheets.add(before=before, after=after)

    def get_worksheet(self, key: Union[int, str]) -> Worksheet:
        """
        获取工作表

        Args:
            key: 索引或名称

        Returns:
            Worksheet 对象
        """
        return self.worksheets.get(key)

    def print_out(self, copies: int = 1,
                  preview: bool = False,
                  active_printer: str = None,
                  print_to_file: bool = False,
                  collate: bool = True):
        """
        打印

        Args:
            copies: 份数
            preview: 是否预览
            active_printer: 打印机
            print_to_file: 打印到文件
            collate: 是否逐份打印
        """
        try:
            if preview:
                self._workbook.PrintPreview()
            else:
                self._workbook.PrintOut(
                    Copies=copies,
                    ActivePrinter=active_printer,
                    PrintToFile=print_to_file,
                    Collate=collate
                )
        except Exception as e:
            raise WorkbookNotFoundError(f"打印失败: {e}")

    def export_as_pdf(self, file_path: str,
                      quality: int = 0,  # xlQualityStandard
                      include_doc_props: bool = True,
                      ignore_print_areas: bool = False):
        """
        导出为 PDF

        Args:
            file_path: 保存路径
            quality: 质量
            include_doc_props: 包含文档属性
            ignore_print_areas: 忽略打印区域
        """
        try:
            self._workbook.ExportAsFixedFormat(
                Type=0,  # xlTypePDF
                Filename=file_path,
                Quality=quality,
                IncludeDocProperties=include_doc_props,
                IgnorePrintAreas=ignore_print_areas
            )
        except Exception as e:
            raise WorkbookNotFoundError(f"导出 PDF 失败: {e}")

    def export_as_xps(self, file_path: str):
        """
        导出为 XPS

        Args:
            file_path: 保存路径
        """
        try:
            self._workbook.ExportAsFixedFormat(
                Type=1,  # xlTypeXPS
                Filename=file_path
            )
        except Exception as e:
            raise WorkbookNotFoundError(f"导出 XPS 失败: {e}")
