from typing import Optional, Any, List, Dict

from .result import Result


# 分页结果核心类（对应PHP的PageResult）
class PageResult(Result):
    def __init__(self, list_data: Optional[List[Any]] = None):
        """
        构造函数
        :param list_data: 分页数据列表，对应PHP中的$list
        """
        # 初始化分页结果字典（对应PHP中的protected $result数组）
        # 遵循Python私有属性命名规范，用下划线标识受保护属性
        self._result: Dict[str, Any] = {'list': list_data if list_data is not None else []}
        # 初始化列表数据，若传入None则设为空列表避免后续报错

    # ------------------------------ 核心分页字段get/set方法 ------------------------------
    def get_total(self) -> Optional[int]:
        """获取总记录数"""
        return self._result.get('total')

    def set_total(self, total: int) -> None:
        """设置总记录数"""
        self._result['total'] = total

    def get_list(self) -> Optional[List[Any]]:
        """获取分页数据列表"""
        return self._result.get('list')

    def set_list(self, list_data: Optional[List[Any]]) -> None:
        """
        设置分页数据列表，并自动更新当前页数据条数（size）
        对应PHP中count($this->result['list'])，Python中用len()获取列表长度
        """
        # 处理None值，确保len()调用不报错
        self._result['list'] = list_data if list_data is not None else []
        # 自动设置当前页数据条数（size）
        self._result['size'] = len(self._result['list'])

    def set_page_num(self, page_num: int) -> None:
        """设置当前页码（pageNum）"""
        self._result['pageNum'] = page_num

    def get_page_size(self) -> Optional[int]:
        """获取每页显示条数（pageSize）"""
        return self._result.get('pageSize')

    def set_page_size(self, page_size: int) -> None:
        """设置每页显示条数（pageSize）"""
        self._result['pageSize'] = page_size

    def get_page_num(self) -> Optional[int]:
        """获取当前页码（pageNum）"""
        return self._result.get('pageNum')

    def get_size(self) -> Optional[int]:
        """获取当前页实际数据条数（size）"""
        return self._result.get('size')

    def set_size(self, size: int) -> None:
        """手动设置当前页实际数据条数（size）"""
        self._result['size'] = size

    def get_pages(self) -> Optional[int]:
        """获取总页数（pages）"""
        return self._result.get('pages')

    def set_pages(self, pages: int) -> None:
        """设置总页数（pages）"""
        self._result['pages'] = pages

    def get_start_row(self) -> Optional[int]:
        """获取当前页起始行号（startRow）"""
        return self._result.get('startRow')

    def set_start_row(self, start_row: int) -> None:
        """设置当前页起始行号（startRow）"""
        self._result['startRow'] = start_row

    def get_end_row(self) -> Optional[int]:
        """获取当前页结束行号（endRow）"""
        return self._result.get('endRow')

    def set_end_row(self, end_row: int) -> None:
        """设置当前页结束行号（endRow）"""
        self._result['endRow'] = end_row

    def get_pre_page(self) -> Optional[int]:
        """获取上一页页码（prePage）"""
        return self._result.get('prePage')

    def set_pre_page(self, pre_page: int) -> None:
        """设置上一页页码（prePage）"""
        self._result['prePage'] = pre_page

    def get_next_page(self) -> Optional[int]:
        """获取下一页页码（nextPage）"""
        return self._result.get('nextPage')

    def set_next_page(self, next_page: int) -> None:
        """设置下一页页码（nextPage）"""
        self._result['nextPage'] = next_page

    def get_is_first_page(self) -> Optional[bool]:
        """判断是否为第一页（isFirstPage）"""
        return self._result.get('isFirstPage')

    def set_is_first_page(self, is_first_page: bool) -> None:
        """设置是否为第一页（isFirstPage）"""
        self._result['isFirstPage'] = is_first_page

    def get_is_last_page(self) -> Optional[bool]:
        """判断是否为最后一页（isLastPage）"""
        return self._result.get('isLastPage')

    def set_is_last_page(self, is_last_page: bool) -> None:
        """设置是否为最后一页（isLastPage）"""
        self._result['isLastPage'] = is_last_page

    def get_has_previous_page(self) -> Optional[bool]:
        """判断是否有上一页（hasPreviousPage）"""
        return self._result.get('hasPreviousPage')

    def set_has_previous_page(self, has_previous_page: bool) -> None:
        """设置是否有上一页（hasPreviousPage）"""
        self._result['hasPreviousPage'] = has_previous_page

    def get_has_next_page(self) -> Optional[bool]:
        """判断是否有下一页（hasNextPage）"""
        return self._result.get('hasNextPage')

    def set_has_next_page(self, has_next_page: bool) -> None:
        """设置是否有下一页（hasNextPage）"""
        self._result['hasNextPage'] = has_next_page

    def get_page_no(self) -> Optional[int]:
        """获取当前页码（pageNo，与pageNum冗余，保持原类字段）"""
        return self._result.get('pageNo')

    def set_page_no(self, page_no: int) -> None:
        """设置当前页码（pageNo，与pageNum冗余，保持原类字段）"""
        self._result['pageNo'] = page_no

    def is_has_next_page(self) -> Optional[bool]:
        """判断是否有下一页（isHasNextPage，与hasNextPage冗余，保持原类方法）"""
        return self._result.get('isHasNextPage')

    def set_is_has_next_page(self, is_has_next_page: bool) -> None:
        """设置是否有下一页（isHasNextPage，与hasNextPage冗余，保持原类方法）"""
        self._result['isHasNextPage'] = is_has_next_page

    # ------------------------------ 核心结果获取/设置方法 ------------------------------
    def get_result(self) -> Dict[str, Any]:
        """获取完整的分页结果字典"""
        return self._result

    def set_result(self, result: Dict[str, Any]) -> None:
        """覆盖设置完整的分页结果字典"""
        self._result = result