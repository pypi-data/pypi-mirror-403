from enum import Enum


class ExcelType(Enum):
    OFFICE = ("Excel.Application", "EXCEL.EXE", "Office")
    WPS = ("KET.Application", "wps.exe", "Wps")


class Platform(Enum):
    """
    指定生成文本文件的平台
    """
    xlMacintosh = 1  # macintosh
    xlMSDOS = 3  # MS-DOS
    xlWindows = 2  # Winodws


class SeparatorFormat(Enum):
    """
    sep_format 使用 确定文件的分隔符
    """
    Tab = 1  # \t
    Commas = 2  # 逗号
    Spaces = 3  # 空格
    Semicolons = 4  # 分号
    Noting = 5  # 无
    Custom = 6  # 自定义字符


class CorruptLoad(Enum):
    """
    指定文件打开时处理
    """
    xlNormalLoad = 0 # 正常打开工作簿
    xlRepairFile = 1 # 尝试修复文件
    xlExtractData = 2 # 尝试恢复工作簿中的数据


class BorderWeight(Enum):
    """边框粗细"""
    HAIRLINE = 1
    THIN = 2
    MEDIUM = -4138
    THICK = 4


class BorderLineStyle(Enum):
    """边框线型"""
    NONE = -4142
    CONTINUOUS = 1
    DASH = -4115
    DOT = -4118
    DASH_DOT = 4
    DASH_DOT_DOT = 5
    DOUBLE = -4119


class SortOrder(Enum):
    """排序顺序"""
    ASCENDING = 1
    DESCENDING = 2


class FilterOperator(Enum):
    """筛选运算符"""
    AND = 1
    OR = 2


class PageOrientation(Enum):
    """页面方向"""
    PORTRAIT = 1
    LANDSCAPE = 2


class PaperSize(Enum):
    """纸张大小"""
    LETTER = 1
    A4 = 9
    A5 = 11
