import time
from typing import Optional, Any, Dict, List

from . import PageResult
from ..lang import HttpStatusCode


# 核心JSON响应结果类（对应PHP的JsonResult）
class JsonResult:
    def __init__(self, data: Optional[Any] = None):
        """
        构造函数
        :param data: 响应核心业务数据
        """
        # 初始化响应结果字典（对应PHP中的$result数组）
        self._result: Dict[str, Any] = {}
        # 设置初始数据
        self.set_data(data)
        # 初始化日志列表（对应PHP中的Console::$lines）
        self.set_logs([])

    # ------------------------------ 静态工厂方法（成功响应）------------------------------
    @staticmethod
    def ok(data: Optional[Any] = None,
           message: str = HttpStatusCode.OK["message"],
           code: int = HttpStatusCode.OK["code"]) -> Dict[str, Any]:
        """创建成功响应（200 OK）"""
        return JsonResult.success(data, message, code)

    @staticmethod
    def suc(data: Optional[Any] = None,
            message: str = HttpStatusCode.OK["message"],
            code: int = HttpStatusCode.OK["code"]) -> Dict[str, Any]:
        """创建成功响应（简短别名，200 OK）"""
        return JsonResult.success(data, message, code)

    @staticmethod
    def success(data: Optional[Any] = None,
                message: str = HttpStatusCode.OK["message"],
                code: int = HttpStatusCode.OK["code"]) -> Dict[str, Any]:
        """创建成功响应（核心方法，200 OK）"""
        r = JsonResult()
        r.set_code(code)
        r.set_message(message)
        r.set_name(HttpStatusCode.OK["name"])
        r.set_timestamp(int(time.time()))
        r.set_success(True)
        r.set_data(data)
        return r.get_result()

    # ------------------------------ 静态工厂方法（失败响应）------------------------------
    @staticmethod
    def fail(message: str = HttpStatusCode.INTERNAL_SERVER_ERROR["message"],
             code: int = HttpStatusCode.INTERNAL_SERVER_ERROR["code"],
             data: Optional[Any] = None) -> Dict[str, Any]:
        """创建失败响应（500 服务器内部错误）"""
        return JsonResult.error(message, code, data)

    @staticmethod
    def err(message: str = HttpStatusCode.INTERNAL_SERVER_ERROR["message"],
            code: int = HttpStatusCode.INTERNAL_SERVER_ERROR["code"],
            data: Optional[Any] = None) -> Dict[str, Any]:
        """创建失败响应（简短别名，500 服务器内部错误）"""
        return JsonResult.error(message, code, data)

    @staticmethod
    def error(message: str = HttpStatusCode.INTERNAL_SERVER_ERROR["message"],
              code: int = HttpStatusCode.INTERNAL_SERVER_ERROR["code"],
              data: Optional[Any] = None) -> Dict[str, Any]:
        """创建失败响应（核心方法，500 服务器内部错误）"""
        r = JsonResult()
        r.set_code(code)
        r.set_message(message)
        r.set_name(HttpStatusCode.INTERNAL_SERVER_ERROR["name"])
        r.set_timestamp(int(time.time()))
        r.set_success(False)
        r.set_data(data)
        return r.get_result()

    # ------------------------------ 静态工厂方法（特殊状态响应）------------------------------
    @staticmethod
    def created(data: Optional[Any] = None,
                message: str = HttpStatusCode.CREATED["message"],
                code: int = HttpStatusCode.CREATED["code"]) -> Dict[str, Any]:
        """创建资源创建成功响应（201 Created）"""
        r = JsonResult()
        r.set_timestamp(int(time.time()))
        r.set_code(code)
        r.set_message(message)
        r.set_name(HttpStatusCode.CREATED["name"])
        r.set_success(True)
        r.set_data(data)
        return r.get_result()

    @staticmethod
    def unfound() -> Dict[str, Any]:
        """创建资源未找到响应（404 Not Found）"""
        r = JsonResult()
        r.set_timestamp(int(time.time()))
        r.set_code(HttpStatusCode.NOT_FOUND["code"])
        r.set_message(HttpStatusCode.NOT_FOUND["message"])
        r.set_name(HttpStatusCode.NOT_FOUND["name"])
        r.set_success(False)
        return r.get_result()

    @staticmethod
    def unauthorized(message: str = HttpStatusCode.UNAUTHORIZED["message"]) -> Dict[str, Any]:
        """创建未授权响应（401 Unauthorized）"""
        r = JsonResult()
        r.set_timestamp(int(time.time()))
        r.set_code(HttpStatusCode.UNAUTHORIZED["code"])
        r.set_message(message)
        r.set_name(HttpStatusCode.UNAUTHORIZED["name"])
        r.set_success(False)
        return r.get_result()

    @staticmethod
    def forbidden(message: str = HttpStatusCode.FORBIDDEN["message"]) -> Dict[str, Any]:
        """创建禁止访问响应（403 Forbidden）"""
        r = JsonResult()
        r.set_timestamp(int(time.time()))
        r.set_code(HttpStatusCode.FORBIDDEN["code"])
        r.set_message(message)
        r.set_name(HttpStatusCode.FORBIDDEN["name"])
        r.set_success(False)
        return r.get_result()

    @staticmethod
    def bad_request(message: str = HttpStatusCode.BAD_REQUEST["message"]) -> Dict[str, Any]:
        """创建请求参数错误响应（400 Bad Request）"""
        r = JsonResult()
        r.set_timestamp(int(time.time()))
        r.set_code(HttpStatusCode.BAD_REQUEST["code"])
        r.set_message(message)
        r.set_name(HttpStatusCode.BAD_REQUEST["name"])
        r.set_success(False)
        return r.get_result()

    @staticmethod
    def request_timeout(message: str = HttpStatusCode.REQUEST_TIMEOUT["message"]) -> Dict[str, Any]:
        """创建请求超时响应（408 Request Timeout）"""
        r = JsonResult()
        r.set_timestamp(int(time.time()))
        r.set_code(HttpStatusCode.REQUEST_TIMEOUT["code"])
        r.set_message(message)
        r.set_name(HttpStatusCode.REQUEST_TIMEOUT["name"])
        r.set_success(False)
        return r.get_result()

    @staticmethod
    def validation_error(message: str = HttpStatusCode.UNPROCESSABLE_ENTITY["message"],
                         data: Optional[Any] = None) -> Dict[str, Any]:
        """创建参数验证失败响应（422 Unprocessable Entity）"""
        r = JsonResult()
        r.set_timestamp(int(time.time()))
        r.set_code(HttpStatusCode.UNPROCESSABLE_ENTITY["code"])
        r.set_message(message)
        r.set_name(HttpStatusCode.UNPROCESSABLE_ENTITY["name"])
        r.set_success(False)
        r.set_data(data)
        return r.get_result()

    # ------------------------------ 核心get/set方法（围绕_result字典）------------------------------
    def get_code(self) -> Optional[int]:
        return self._result.get("code")

    def set_code(self, code: int) -> None:
        self._result["code"] = code

    def get_name(self) -> Optional[str]:
        return self._result.get("name")

    def set_name(self, name: str) -> None:
        self._result["name"] = name

    def get_msg(self) -> Optional[str]:
        """别名方法：获取响应消息"""
        return self.get_message()

    def set_msg(self, msg: str) -> None:
        """别名方法：设置响应消息"""
        self.set_message(msg)

    def get_message(self) -> Optional[str]:
        return self._result.get("message")

    def set_message(self, message: str) -> None:
        self._result["message"] = message

    def get_timestamp(self) -> Optional[int]:
        return self._result.get("timestamp")

    def set_timestamp(self, timestamp: int) -> None:
        self._result["timestamp"] = timestamp

    def get_success(self) -> Optional[bool]:
        return self._result.get("success")

    def set_success(self, success: bool) -> None:
        self._result["success"] = success
        self._result["isSuccess"] = 1 if success else 0

    def get_is_success(self) -> Optional[int]:
        return self._result.get("isSuccess")

    def set_is_success(self, is_success: int) -> None:
        self._result["isSuccess"] = is_success
        self._result["success"] = (is_success == 1)

    def get_data(self) -> Optional[Any]:
        return self._result.get("data")

    def set_data(self, data: Optional[Any]) -> None:
        """处理分页结果，适配原类逻辑"""
        if isinstance(data, PageResult):
            self._result["data"] = data.get_result()
        else:
            self._result["data"] = data

    def get_logs(self) -> Optional[List[Any]]:
        return self._result.get("logs", [])

    def set_logs(self, logs: List[Any]) -> None:
        self._result["logs"] = logs

    # ------------------------------ 其他扩展get/set方法（保持原类字段完整性）------------------------------
    def get_hash(self) -> Optional[str]:
        return self._result.get("hash")

    def set_hash(self, hash_val: str) -> None:
        self._result["hash"] = hash_val

    def get_type(self) -> Optional[str]:
        return self._result.get("type")

    def set_type(self, type_val: str) -> None:
        self._result["type"] = type_val

    def get_version(self) -> Optional[str]:
        return self._result.get("version")

    def set_version(self, version: str) -> None:
        self._result["version"] = version

    def get_result(self, raw: bool = True) -> Dict[str, Any]:
        """
        获取最终响应结果
        :param raw: 是否返回原生字典（保持参数兼容性，无实际逻辑差异）
        :return: 标准化响应字典
        """
        return self._result

    def set_result(self, result: Dict[str, Any]) -> None:
        self._result = result
