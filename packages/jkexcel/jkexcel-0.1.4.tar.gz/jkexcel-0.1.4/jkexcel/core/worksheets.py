from typing import List, Optional, Iterator, Union
import win32com.client

from jkexcel.core.worksheet import Worksheet
from jkexcel.models.exceptions import WorksheetNotFoundError


class Worksheets:
    """Excel 工作表集合封装类"""

    def __init__(self, com_worksheets):
        """
        初始化 Worksheets

        Args:
            com_worksheets: COM Worksheets 对象
        """
        if com_worksheets is None:
            raise WorksheetNotFoundError("COM Worksheets 对象不能为 None")
        self._worksheets = com_worksheets

    def __repr__(self) -> str:
        return f"<Worksheets count={self.count}>"

    def __len__(self) -> int:
        """获取工作表数量"""
        return self.count

    def __getitem__(self, key: Union[int, str]) -> Worksheet:
        """通过索引或名称获取工作表"""
        return self.get(key)

    def __iter__(self) -> Iterator[Worksheet]:
        """迭代工作表"""
        for i in range(1, self.count + 1):
            yield self.get(i)

    @property
    def com_object(self):
        """获取底层 COM 对象"""
        return self._worksheets

    @property
    def count(self) -> int:
        """获取工作表数量"""
        try:
            return self._worksheets.Count
        except Exception as e:
            raise WorksheetNotFoundError(f"获取工作表数量失败: {e}")

    @property
    def names(self) -> List[str]:
        """获取所有工作表名称"""
        return [sheet.name for sheet in self]

    def get(self, key: Union[int, str]) -> Worksheet:
        """
        获取工作表

        Args:
            key: 索引（从1开始）或名称

        Returns:
            Worksheet 对象
        """
        try:
            if isinstance(key, int):
                com_sheet = self._worksheets(key)
            else:
                com_sheet = self._worksheets(key)
            return Worksheet(com_sheet)
        except Exception as e:
            raise WorksheetNotFoundError(f"获取工作表失败: {e}")

    def add(self, before: Optional[Union[int, str, Worksheet]] = None,
            after: Optional[Union[int, str, Worksheet]] = None,
            count: int = 1) -> Union[Worksheet, List[Worksheet]]:
        """
        添加新工作表

        Args:
            before: 插入到指定工作表之前
            after: 插入到指定工作表之后
            count: 添加数量

        Returns:
            Worksheet 对象或列表
        """
        try:
            if count == 1:
                if before:
                    if isinstance(before, Worksheet):
                        com_sheet = self._worksheets.Add(Before=before.com_object)
                    else:
                        com_sheet = self._worksheets.Add(Before=self.get(before).com_object)
                elif after:
                    if isinstance(after, Worksheet):
                        com_sheet = self._worksheets.Add(After=after.com_object)
                    else:
                        com_sheet = self._worksheets.Add(After=self.get(after).com_object)
                else:
                    com_sheet = self._worksheets.Add()
                return Worksheet(com_sheet)
            else:
                sheets = []
                for _ in range(count):
                    if before:
                        com_sheet = self._worksheets.Add(Before=self.get(before).com_object)
                    elif after:
                        com_sheet = self._worksheets.Add(After=self.get(after).com_object)
                    else:
                        com_sheet = self._worksheets.Add()
                    sheets.append(Worksheet(com_sheet))
                return sheets
        except Exception as e:
            raise WorksheetNotFoundError(f"添加工作表失败: {e}")

    def delete(self, key: Union[int, str, Worksheet]):
        """
        删除工作表

        Args:
            key: 索引、名称或 Worksheet 对象
        """
        try:
            if isinstance(key, Worksheet):
                sheet = key
            else:
                sheet = self.get(key)
            sheet.delete()
        except Exception as e:
            raise WorksheetNotFoundError(f"删除工作表失败: {e}")

    def exists(self, name: str) -> bool:
        """
        检查工作表是否存在

        Args:
            name: 工作表名称

        Returns:
            bool
        """
        try:
            self._worksheets(name)
            return True
        except:
            return False

    def rename(self, old_name: str, new_name: str):
        """
        重命名工作表

        Args:
            old_name: 旧名称
            new_name: 新名称
        """
        try:
            sheet = self.get(old_name)
            sheet.name = new_name
        except Exception as e:
            raise WorksheetNotFoundError(f"重命名工作表失败: {e}")

    def move(self, sheet_key: Union[int, str, Worksheet],
             before: Optional[Union[int, str, Worksheet]] = None,
             after: Optional[Union[int, str, Worksheet]] = None):
        """
        移动工作表

        Args:
            sheet_key: 要移动的工作表
            before: 移动到指定工作表之前
            after: 移动到指定工作表之后
        """
        try:
            if isinstance(sheet_key, Worksheet):
                sheet = sheet_key
            else:
                sheet = self.get(sheet_key)

            if before:
                if isinstance(before, Worksheet):
                    sheet.move(before=before)
                else:
                    sheet.move(before=self.get(before))
            elif after:
                if isinstance(after, Worksheet):
                    sheet.move(after=after)
                else:
                    sheet.move(after=self.get(after))
            else:
                sheet.move()
        except Exception as e:
            raise WorksheetNotFoundError(f"移动工作表失败: {e}")

    def copy(self, sheet_key: Union[int, str, Worksheet],
             before: Optional[Union[int, str, Worksheet]] = None,
             after: Optional[Union[int, str, Worksheet]] = None) -> Worksheet:
        """
        复制工作表

        Args:
            sheet_key: 要复制的工作表
            before: 复制到指定工作表之前
            after: 复制到指定工作表之后

        Returns:
            新的 Worksheet 对象
        """
        try:
            if isinstance(sheet_key, Worksheet):
                sheet = sheet_key
            else:
                sheet = self.get(sheet_key)

            if before:
                if isinstance(before, Worksheet):
                    new_sheet = sheet.copy(before=before)
                else:
                    new_sheet = sheet.copy(before=self.get(before))
            elif after:
                if isinstance(after, Worksheet):
                    new_sheet = sheet.copy(after=after)
                else:
                    new_sheet = sheet.copy(after=self.get(after))
            else:
                new_sheet = sheet.copy()

            return new_sheet
        except Exception as e:
            raise WorksheetNotFoundError(f"复制工作表失败: {e}")

    def hide(self, sheet_key: Union[int, str, Worksheet]):
        """
        隐藏工作表

        Args:
            sheet_key: 工作表标识
        """
        try:
            if isinstance(sheet_key, Worksheet):
                sheet = sheet_key
            else:
                sheet = self.get(sheet_key)
            sheet.visible = False
        except Exception as e:
            raise WorksheetNotFoundError(f"隐藏工作表失败: {e}")

    def show(self, sheet_key: Union[int, str, Worksheet]):
        """
        显示工作表

        Args:
            sheet_key: 工作表标识
        """
        try:
            if isinstance(sheet_key, Worksheet):
                sheet = sheet_key
            else:
                sheet = self.get(sheet_key)
            sheet.visible = True
        except Exception as e:
            raise WorksheetNotFoundError(f"显示工作表失败: {e}")

    def get_by_index(self, index: int) -> Worksheet:
        """通过索引获取工作表（别名）"""
        return self.get(index)

    def get_by_name(self, name: str) -> Worksheet:
        """通过名称获取工作表（别名）"""
        return self.get(name)

    def index_of(self, name: str) -> Optional[int]:
        """
        获取工作表索引

        Args:
            name: 工作表名称

        Returns:
            索引或 None
        """
        for i, sheet in enumerate(self, 1):
            if sheet.name == name:
                return i
        return None