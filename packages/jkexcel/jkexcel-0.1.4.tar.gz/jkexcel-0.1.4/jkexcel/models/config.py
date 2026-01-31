from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Literal
from enum import Enum

from jkexcel.models.enums import ExcelType


class SaveFormat(Enum):
    """保存格式枚举"""
    xlAddIn = (18, ".xla")  # Microsoft Excel 97-2003 外接程序
    xlAddIn8 = (18, ".xla")  # Microsoft Excel 97-2003 外接程序
    xlCSV = (6, ".csv")  # CSV
    xlCSVMac = (22, ".csv")  # Macintosh CSV
    xlCSVMSDOS = (24, ".csv")  # MSDOS CSV
    xlCSVUTF8 = (62, ".csv")  # UTF8 CSV
    xlCSVWindows = (23, ".csv")  # Windows CSV
    xlCurrentPlatformText = (-4158, ".txt")  # 当前平台文本
    xlDBF2 = (7, ".dbf")  # Dbase2
    xlDBF3 = (8, ".dbf")  # Dbase3
    xlDBF4 = (11, ".dbf")  # Dbase4
    xlDIF = (9, ".dif")  # 数据交换格式
    xlExcel12 = (50, ".xlsb")  # xlExcel12
    xlExcel2 = (16, ".xls")  # Excel 2.0 (1987)
    xlExcel2FarEast = (27, ".xls")  # Excel 2.0 Asia (1987)
    xlExcel3 = (29, ".xls")  # Excel 3.0 (1990)
    xlExcel4 = (33, ".xls")  # Excel 4.0 (1992)
    xlExcel4Workbook = (34, ".xls")  # Excel 4.0 工作簿格式 (1992)
    xlExcel5 = (39, ".xls")  # Excel 5.0 (1994)
    xlExcel7 = (39, ".xls")  # Excel 95 7.0
    xlExcel8 = (56, ".xls")  # Excel 97-2003 工作簿
    xlExcel9795 = (43, ".xls")  # Excel 95 和 97
    xlHtml = (44, ".html")  # HTML
    xlIntlAddIn = (26, "")  # 国际外接程序
    xlIntlMacro = (25, "")  # 国际宏
    xlOpenDocumentSpreadsheet = (60, ".ods")  # OpenDocument电子表格
    xlOpenXMLAddIn = (55, ".xlam")  # Open XML 外接程序
    xlOpenXMLStrictWorkbook = (61, ".xlsx")  # Strict Open XML 文件
    xlOpenXMLTemplate = (54, ".xltx")  # Open XML 模板
    xlOpenXMLTemplateMacroEnabled = (53, ".xltm")  # 启用 Open XML 模板宏
    xlOpenXMLWorkbook = (51, ".xlsx")  # Open XML 工作簿
    xlOpenXMLWorkbookMacroEnabled = (52, ".xlsm")  # 启用 Open XML 工作簿宏
    xlSYLK = (2, ".slk")  # 符号链接格式
    xlTemplate = (17, ".xlt")  # Excel 模板格式
    xlTemplate8 = (17, ".xlt")  # 模板 8
    xlTextMac = (19, ".txt")  # Macintosh 文本
    xlTextMSDOS = (21, ".txt")  # MSDOS 文本
    xlTextPrinter = (36, ".prn")  # 打印机文本
    xlTextWindows = (20, ".txt")  # Windows 文本
    xlUnicodeText = (42, "")  # Unicode 文本
    xlWebArchive = (45, ".mhtml")  # Web 档案
    xlWJ2WD1 = (14, ".wj2")  # 日语1-2-3
    xlWJ3 = (40, ".wj3")  # 日语1-2-3
    xlWJ3FJ3 = (41, ".wj3")  # 日语1-2-3 格式
    xlWK1 = (5, ".wk1")  # Lotus 1-2-3 格式
    xlWK1ALL = (31, ".wk1")  # Lotus 1-2-3 格式
    xlWK1FMT = (30, ".wk1")  # Lotus 1-2-3 格式
    xlWK3 = (15, ".wk3")  # Lotus 1-2-3 格式
    xlWK3FM3 = (32, ".wk3")  # Lotus 1-2-3 格式
    xlWK4 = (38, ".wk4")  # Lotus 1-2-3 格式
    xlWKS = (4, ".wks")  # Lotus 1-2-3 格式
    xlWorkbookDefault = (51, ".xlsx")  # 默认工作簿
    xlWorkbookNormal = (-4143, ".xls")  # 常规工作簿
    xlWorks2FarEast = (28, ".wks")  # Microsoft Works 2.0 亚洲格式
    xlWQ1 = (34, ".wq1")  # Quattro Pro 格式
    xlXMLSpreadsheet = (46, ".xml")  # XML 电子表格


class SaveAsAccessMode(Enum):
    """
    指定另存为函数访问模式
    """
    xlExclusive = (3, "独占模式")
    xlNoChange = (1, "不更改访问模式")
    xlShared = (2, "共享模式")


class SaveConflictResolution(Enum):
    """
    指定更新共享工作簿时解决冲突的方式
    """
    xlLocalSessionChanges = (2, "总是接受本地用户所做的更改")
    xlOtherSessionChanges = (3, "总是拒绝本地用户所做的更改")
    xlUserResolution = (1, "弹出对话框请求用户解决冲突")


class SheetVisibility(Enum):
    """工作表可见性枚举"""
    VISIBLE = -1
    HIDDEN = 0
    VERY_HIDDEN = 2


@dataclass
class ExcelConfig:
    """Excel 配置"""
    driver: ExcelType = ExcelType.OFFICE
    visible: bool = True # 窗口可见
    display_alerts: bool = False # 警告弹窗
    screen_updating: bool = True # 屏幕刷新
    enable_events: bool = True
    user_control: bool = True # 是否启用用户控制
    window_state: Literal["normal", "minimized", "maximized"] = "normal" # 启动后是否最大化窗口
    read_only_recommended: bool = False
    update_links: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {k: v.value if isinstance(v, Enum) else v
                for k, v in self.__dict__.items()}


@dataclass
class RangeStyle:
    """范围样式配置"""
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    font_bold: Optional[bool] = None
    font_italic: Optional[bool] = None
    font_color: Optional[int] = None
    font_color_rgb: Optional[Tuple[int, int, int]] = None
    fill_color: Optional[int] = None
    fill_color_rgb: Optional[Tuple[int, int, int]] = None
    horizontal_alignment: Optional[int] = None
    vertical_alignment: Optional[int] = None
    number_format: Optional[str] = None
    wrap_text: Optional[bool] = None
    borders: Optional[Dict[str, Any]] = None

    class Colors:
        """颜色常量"""
        BLACK = 0x000000
        WHITE = 0xFFFFFF
        RED = 0xFF0000
        GREEN = 0x00FF00
        BLUE = 0x0000FF
        YELLOW = 0xFFFF00
        ORANGE = 0xFF6600
        GRAY = 0xC0C0C0
        LIGHT_GRAY = 0xF0F0F0

    class Alignment:
        """对齐方式常量"""
        LEFT = -4131
        CENTER = -4108
        RIGHT = -4152
        TOP = -4160
        MIDDLE = -4108
        BOTTOM = -4107
        JUSTIFY = -4130
