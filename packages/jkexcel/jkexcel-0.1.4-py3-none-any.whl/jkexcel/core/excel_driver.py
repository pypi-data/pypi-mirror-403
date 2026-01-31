import pywintypes
import win32con
import ctypes
import ctypes.wintypes
import psutil
import win32com.client
import win32security
import win32api
from typing import Optional, List, Tuple, Any

from jkexcel.models.enums import ExcelType
from jkexcel.models.exceptions import ExecutionFaultedException

# Windows API常量/函数封装（对应C#的P/Invoke）
user32 = ctypes.WinDLL("user32.dll", use_last_error=True)
oleacc = ctypes.WinDLL("oleacc.dll", use_last_error=True)

# 定义Windows API参数类型
user32.EnumChildWindows.argtypes = [
    ctypes.wintypes.HWND,
    ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.py_object),
    ctypes.py_object
]
user32.EnumChildWindows.restype = ctypes.c_bool

user32.GetClassNameW.argtypes = [
    ctypes.wintypes.HWND,
    ctypes.wintypes.LPWSTR,
    ctypes.c_int
]
user32.GetClassNameW.restype = ctypes.c_int

# COM相关常量
IID_IUnknown = pywintypes.IID("{00000000-0000-0000-C000-000000000046}")
DW_OBJECT_ID = 0xFFFFFFF0  # 对应C#的4294967280u


class ExcelApplicationService:
    @staticmethod
    def create_default_application() -> Any:
        """创建默认Excel/WPS应用实例（优先Office，失败则WPS）"""
        try:
            # 优先创建Office Excel
            app = win32com.client.Dispatch(ExcelType.OFFICE.value[0])
            return app
        except Exception as ex:
            # 捕获COM异常，尝试创建Office/WPS
            error_msg = str(ex)
            wps_guid1 = "00024500-0000-0000-C000-000000000046"
            wps_guid2 = "45540001-5750-5300-4B49-4E47534F4655"
            if wps_guid1 in error_msg or wps_guid2 in error_msg:
                raise ExecutionFaultedException(f"启动{ExcelType.WPS.value[2]}失败")
            # 依次尝试Office→WPS
            office_app = ExcelApplicationService.create_application(ExcelType.OFFICE)
            if office_app:
                return office_app
            wps_app = ExcelApplicationService.create_application(ExcelType.WPS)
            if wps_app:
                return wps_app
            raise ExecutionFaultedException("启动Excel/WPS应用失败")

    @staticmethod
    def create_application(excel_type: ExcelType, throw_exception: bool = False) -> Optional[Any]:
        """创建指定类型的Excel/WPS应用实例"""
        try:
            app = win32com.client.Dispatch(excel_type.value[0])
            return app
        except Exception:
            if throw_exception:
                raise ExecutionFaultedException(f"启动{excel_type.value[2]}应用失败")
            return None

    @staticmethod
    def is_admin_process(process: psutil.Process) -> bool:
        """校验进程是否以管理员权限运行"""
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, process.pid)
            token = win32security.OpenProcessToken(handle, win32security.TOKEN_QUERY)
            sid = win32security.GetTokenInformation(token, win32security.TokenElevationType)
            return sid in [
                win32security.TokenElevationTypeFull,
                win32security.TokenElevationTypeLimited,
            ]
        except:
            return True

    @staticmethod
    def _is_current_user_admin() -> bool:
        """
        检查当前用户是否是管理员
        管理员账号有两个令牌: Full 和 Limited
        普通只有一个: Default
        """
        try:
            # 获取当前进程令牌
            token_handle = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(),
                win32security.TOKEN_QUERY
            )
            # 获取令牌信息
            token_info = win32security.GetTokenInformation(
                token_handle,
                win32security.TokenElevationType
            )
            # 关闭令牌句柄
            win32api.CloseHandle(token_handle)
            # 检查是否为管理员
            return token_info in [
                win32security.TokenElevationTypeFull,  # 完整管理员令牌
                win32security.TokenElevationTypeLimited,  # 有时是 TokenElevationTypeLimited
            ]

        except Exception:
            return True

    @staticmethod
    def attach_to_running_application(excel_type: ExcelType, throw_exception: bool = False) -> Any:
        """附加到已运行的Excel/WPS进程（核心逻辑）"""
        try:
            # 获取指定名称的进程
            process_name = excel_type.value[1]
            processes = [p for p in psutil.process_iter(['name', 'pid']) if p.name().lower() == process_name.lower()]
            if not processes:
                raise ExecutionFaultedException(f"未找到{process_name}进程")

            # 校验权限一致性
            current_is_admin = ExcelApplicationService._is_current_user_admin()
            target_process = processes[0]
            if current_is_admin != ExcelApplicationService.is_admin_process(target_process):
                if throw_exception:
                    msg = "当前程序与Excel/WPS权限不一致（需同为管理员/非管理员）"
                    raise ExecutionFaultedException(msg)
                return None

            # 枚举窗口并附加到进程
            return ExcelApplicationService._attach_to_process(processes)
        except Exception as ex:
            if throw_exception:
                raise ExecutionFaultedException(str(ex))
            return None

    @staticmethod
    def _attach_to_process(processes: List[psutil.Process]) -> Any:
        """从进程句柄获取Excel/WPS COM对象（对应C#的AttachToRunningExcelProcess）"""
        for process in processes:
            hwnd = ExcelApplicationService._get_main_window_handle(process)
            if hwnd == 0:
                continue
            print(hwnd)
            # 枚举子窗口，筛选Excel/WPS核心窗口
            child_windows = []

            def enum_child_callback(hwnd, extra):
                # 获取窗口类名，匹配"excel 7"（忽略大小写）
                class_name = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, class_name, 256)
                if "excel 7" in class_name.value.lower():
                    child_windows.append(hwnd)
                return True

            enum_callback = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.py_object)(
                enum_child_callback)
            user32.EnumChildWindows(hwnd, enum_callback, None)

            if child_windows:
                # 从窗口句柄获取COM对象
                ptr = ctypes.POINTER(ctypes.c_void_p)()
                res = oleacc.AccessibleObjectFromWindow(
                    child_windows[0], DW_OBJECT_ID, ctypes.byref(IID_IUnknown), ctypes.byref(ptr)
                )
                if res >= 0 and ptr:
                    # 将指针转换为COM对象
                    app = win32com.client.Dispatch(ptr)
                    return app.Application
        raise ExecutionFaultedException("无法附加到Excel/WPS进程")

    @staticmethod
    def _get_main_window_handle(process: psutil.Process) -> Optional[int]:
        """
        从 psutil.Process 对象获取进程的主窗口句柄（对应 C# 的 Process.MainWindowHandle）
        参数:
            process: psutil.Process 对象
        返回:
            int: 主窗口句柄（HWND），无主窗口则返回 None
        """
        pid = process.pid
        main_handle = None

        # 定义枚举窗口的回调函数
        def enum_windows_callback(hwnd: int, lparam: int) -> bool:
            nonlocal main_handle

            # 获取窗口所属进程的 PID
            window_pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))

            # 匹配 PID 且窗口可见
            if window_pid.value == pid and user32.IsWindowVisible(hwnd):
                # 获取窗口标题（主窗口通常有非空标题）
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    main_handle = hwnd
                    return False  # 找到主窗口后停止枚举

            return True

        # 转换回调函数为 Windows 可调用的类型
        callback = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)(
            enum_windows_callback)

        # 枚举所有顶层窗口，查找目标进程的主窗口
        user32.EnumWindows(callback, 0)

        return main_handle

    @staticmethod
    def contain_workbook(excel_app: Any, full_name: str) -> bool:
        """校验Excel/WPS是否包含指定工作簿（对应C#的ContainWorkbook）"""
        for workbook in excel_app.Workbooks:
            if workbook.FullName == full_name and not workbook.ReadOnly:
                workbook.ActiveSheet.Activate()
                return True
        return False
