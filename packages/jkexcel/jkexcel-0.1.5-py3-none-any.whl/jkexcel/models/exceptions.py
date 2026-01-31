class ExcelCOMError(Exception):
    """Excel COM 基础异常"""
    pass


class ExcelNotRunningError(ExcelCOMError):
    """Excel 未运行异常"""
    pass


class WorkbookNotFoundError(ExcelCOMError):
    """工作簿未找到异常"""
    pass


class WorksheetNotFoundError(ExcelCOMError):
    """工作表未找到异常"""
    pass


class RangeError(ExcelCOMError):
    """范围错误异常"""
    pass


class InvalidParameterError(ExcelCOMError):
    """无效参数异常"""
    pass


class FileOperationError(ExcelCOMError):
    """文件操作异常"""
    pass


class PermissionError(ExcelCOMError):
    """权限异常"""
    pass


class COMConnectionError(ExcelCOMError):
    """COM 连接异常"""
    pass


class TimeoutError(ExcelCOMError):
    """超时异常"""
    pass


class ExecutionFaultedException(ExcelCOMError):
    """执行异常"""
    pass
