from typing import List, Tuple, Optional, Dict, Any

from jkexcel.core.worksheet import Worksheet
from jkexcel.models.config import RangeStyle
from jkexcel.utils.validators import validate_range_address


class FormatOperations:
    """格式操作类"""

    def __init__(self, worksheet: Worksheet):
        """
        初始化

        Args:
            worksheet: Worksheet 对象
        """
        self.ws = worksheet

    def apply_table_format(self,
                           range_address: str,
                           style_name: str = "TableStyleMedium9"):
        """
        应用表格格式

        Args:
            range_address: 范围地址
            style_name: 表格样式名称
        """
        validate_range_address(range_address)

        table_range = self.ws.get_range(range_address)

        # 添加表格
        table = self.ws.com_object.ListObjects.Add(
            SourceType=1,  # xlSrcRange
            Source=table_range.com_object,
            XlListObjectHasHeaders=1
        )

        # 应用样式
        table.TableStyle = style_name

    def apply_number_format(self,
                            range_address: str,
                            number_format: str):
        """
        应用数字格式

        Args:
            range_address: 范围地址
            number_format: 数字格式
        """
        validate_range_address(range_address)

        cell_range = self.ws.get_range(range_address)
        cell_range.com_object.NumberFormat = number_format

    def apply_conditional_formatting(self,
                                     range_address: str,
                                     formula: str,
                                     style: RangeStyle):
        """
        应用条件格式

        Args:
            range_address: 范围地址
            formula: 条件公式
            style: 样式
        """
        validate_range_address(range_address)

        cell_range = self.ws.get_range(range_address)

        # 添加条件格式
        cf = cell_range.com_object.FormatConditions.Add(
            Type=2,  # xlExpression
            Formula1=formula
        )

        # 应用样式
        font = cf.Font
        interior = cf.Interior

        if style.font_bold is not None:
            font.Bold = style.font_bold
        if style.font_color is not None:
            font.Color = style.font_color
        if style.fill_color is not None:
            interior.Color = style.fill_color

    def apply_data_validation(self,
                              range_address: str,
                              validation_type: int,
                              formula1: str = "",
                              formula2: str = "",
                              ignore_blank: bool = True,
                              show_error: bool = True,
                              error_title: str = "",
                              error_message: str = ""):
        """
        应用数据验证

        Args:
            range_address: 范围地址
            validation_type: 验证类型
            formula1: 公式1
            formula2: 公式2
            ignore_blank: 是否忽略空值
            show_error: 是否显示错误
            error_title: 错误标题
            error_message: 错误消息
        """
        validate_range_address(range_address)

        cell_range = self.ws.get_range(range_address)

        dv = cell_range.com_object.Validation
        dv.Add(
            Type=validation_type,
            Formula1=formula1,
            Formula2=formula2
        )

        dv.IgnoreBlank = ignore_blank
        dv.ShowError = show_error

        if error_title:
            dv.ErrorTitle = error_title
        if error_message:
            dv.ErrorMessage = error_message