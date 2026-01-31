from typing import Dict, Final


# HTTP状态码常量核心类（对应PHP的HttpStatusCode）
class HttpStatusCode:
    """
    HTTP 状态码常量类
    包含所有标准 HTTP 状态码及其描述信息，用于统一管理系统中的HTTP响应状态。

    字段说明:
    - code: HTTP状态码数字值
    - name: HTTP状态码标准英文名称
    - message: 简体中文描述信息，便于开发人员理解状态码含义

    使用示例:
    HttpStatusCode.OK["code"]        # 200
    HttpStatusCode.NOT_FOUND["name"]  # "Not Found"
    HttpStatusCode.FORBIDDEN["message"] # "禁止访问"
    """

    # ------------------------------ 1xx 信息性状态码 (Informational) ------------------------------
    # 表示请求已被接受，继续处理
    HTTP_CONTINUE: Final[Dict[str, object]] = {
        "code": 100,
        "name": "Continue",
        "message": "继续"
    }

    SWITCHING_PROTOCOLS: Final[Dict[str, object]] = {
        "code": 101,
        "name": "Switching Protocols",
        "message": "切换协议"
    }

    # ------------------------------ 2xx 成功状态码 (Success) ------------------------------
    # 表示请求已成功被服务器接收、理解、并接受
    OK: Final[Dict[str, object]] = {
        "code": 200,
        "name": "OK",
        "message": "请求成功"
    }

    CREATED: Final[Dict[str, object]] = {
        "code": 201,
        "name": "Created",
        "message": "创建成功"
    }

    ACCEPTED: Final[Dict[str, object]] = {
        "code": 202,
        "name": "Accepted",
        "message": "已接受"
    }

    NON_AUTHORITATIVE_INFORMATION: Final[Dict[str, object]] = {
        "code": 203,
        "name": "Non-Authoritative Information",
        "message": "非授权信息"
    }

    NO_CONTENT: Final[Dict[str, object]] = {
        "code": 204,
        "name": "No Content",
        "message": "没有内容"
    }

    RESET_CONTENT: Final[Dict[str, object]] = {
        "code": 205,
        "name": "Reset Content",
        "message": "重置内容"
    }

    PARTIAL_CONTENT: Final[Dict[str, object]] = {
        "code": 206,
        "name": "Partial Content",
        "message": "部分内容"
    }

    # ------------------------------ 3xx 重定向状态码 (Redirection) ------------------------------
    # 表示需要客户端采取进一步的操作才能完成请求
    MULTIPLE_CHOICES: Final[Dict[str, object]] = {
        "code": 300,
        "name": "Multiple Choices",
        "message": "多种选择"
    }

    MOVED_PERMANENTLY: Final[Dict[str, object]] = {
        "code": 301,
        "name": "Moved Permanently",
        "message": "永久移动"
    }

    FOUND: Final[Dict[str, object]] = {
        "code": 302,
        "name": "Found",
        "message": "临时移动"
    }

    SEE_OTHER: Final[Dict[str, object]] = {
        "code": 303,
        "name": "See Other",
        "message": "查看其他位置"
    }

    NOT_MODIFIED: Final[Dict[str, object]] = {
        "code": 304,
        "name": "Not Modified",
        "message": "未修改"
    }

    USE_PROXY: Final[Dict[str, object]] = {
        "code": 305,
        "name": "Use Proxy",
        "message": "使用代理"
    }

    TEMPORARY_REDIRECT: Final[Dict[str, object]] = {
        "code": 307,
        "name": "Temporary Redirect",
        "message": "临时重定向"
    }

    PERMANENT_REDIRECT: Final[Dict[str, object]] = {
        "code": 308,
        "name": "Permanent Redirect",
        "message": "永久重定向"
    }

    # ------------------------------ 4xx 客户端错误状态码 (Client Error) ------------------------------
    # 表示客户端可能出错，妨碍了服务器的处理
    BAD_REQUEST: Final[Dict[str, object]] = {
        "code": 400,
        "name": "Bad Request",
        "message": "请求错误"
    }

    UNAUTHORIZED: Final[Dict[str, object]] = {
        "code": 401,
        "name": "Unauthorized",
        "message": "未授权"
    }

    PAYMENT_REQUIRED: Final[Dict[str, object]] = {
        "code": 402,
        "name": "Payment Required",
        "message": "需要付款"
    }

    FORBIDDEN: Final[Dict[str, object]] = {
        "code": 403,
        "name": "Forbidden",
        "message": "禁止访问"
    }

    NOT_FOUND: Final[Dict[str, object]] = {
        "code": 404,
        "name": "Not Found",
        "message": "服务器无法根据客户端的请求找到资源"
    }

    METHOD_NOT_ALLOWED: Final[Dict[str, object]] = {
        "code": 405,
        "name": "Method Not Allowed",
        "message": "方法不允许"
    }

    NOT_ACCEPTABLE: Final[Dict[str, object]] = {
        "code": 406,
        "name": "Not Acceptable",
        "message": "请求的资源不可用"
    }

    PROXY_AUTHENTICATION_REQUIRED: Final[Dict[str, object]] = {
        "code": 407,
        "name": "Proxy Authentication Required",
        "message": "需要代理认证"
    }

    REQUEST_TIMEOUT: Final[Dict[str, object]] = {
        "code": 408,
        "name": "Request Timeout",
        "message": "请求超时"
    }

    CONFLICT: Final[Dict[str, object]] = {
        "code": 409,
        "name": "Conflict",
        "message": "冲突"
    }

    GONE: Final[Dict[str, object]] = {
        "code": 410,
        "name": "Gone",
        "message": "已删除"
    }

    LENGTH_REQUIRED: Final[Dict[str, object]] = {
        "code": 411,
        "name": "Length Required",
        "message": "需要内容长度"
    }

    PRECONDITION_FAILED: Final[Dict[str, object]] = {
        "code": 412,
        "name": "Precondition Failed",
        "message": "前置条件失败"
    }

    PAYLOAD_TOO_LARGE: Final[Dict[str, object]] = {
        "code": 413,
        "name": "Payload Too Large",
        "message": "请求实体过大"
    }

    URI_TOO_LONG: Final[Dict[str, object]] = {
        "code": 414,
        "name": "URI Too Long",
        "message": "请求的URI过长"
    }

    UNSUPPORTED_MEDIA_TYPE: Final[Dict[str, object]] = {
        "code": 415,
        "name": "Unsupported Media Type",
        "message": "不支持的媒体类型"
    }

    RANGE_NOT_SATISFIABLE: Final[Dict[str, object]] = {
        "code": 416,
        "name": "Range Not Satisfiable",
        "message": "请求范围不符合要求"
    }

    EXPECTATION_FAILED: Final[Dict[str, object]] = {
        "code": 417,
        "name": "Expectation Failed",
        "message": "期望值错误"
    }

    IM_A_TEAPOT: Final[Dict[str, object]] = {
        "code": 418,
        "name": "I'm a teapot",
        "message": "我是一个茶壶"
    }

    UNPROCESSABLE_ENTITY: Final[Dict[str, object]] = {
        "code": 422,
        "name": "Unprocessable Entity",
        "message": "请求格式正确，但是由于含有语义错误，无法响应"
    }

    LOCKED: Final[Dict[str, object]] = {
        "code": 423,
        "name": "Locked",
        "message": "锁定"
    }

    FAILED_DEPENDENCY: Final[Dict[str, object]] = {
        "code": 424,
        "name": "Failed Dependency",
        "message": "依赖失败"
    }

    TOO_EARLY: Final[Dict[str, object]] = {
        "code": 425,
        "name": "Too Early",
        "message": "太早"
    }

    UPGRADE_REQUIRED: Final[Dict[str, object]] = {
        "code": 426,
        "name": "Upgrade Required",
        "message": "需要升级"
    }

    PRECONDITION_REQUIRED: Final[Dict[str, object]] = {
        "code": 428,
        "name": "Precondition Required",
        "message": "需要前置条件"
    }

    TOO_MANY_REQUESTS: Final[Dict[str, object]] = {
        "code": 429,
        "name": "Too Many Requests",
        "message": "请求次数过多"
    }

    REQUEST_HEADER_FIELDS_TOO_LARGE: Final[Dict[str, object]] = {
        "code": 431,
        "name": "Request Header Fields Too Large",
        "message": "请求头字段太大"
    }

    UNAVAILABLE_FOR_LEGAL_REASONS: Final[Dict[str, object]] = {
        "code": 451,
        "name": "Unavailable For Legal Reasons",
        "message": "因法律原因不可用"
    }

    # ------------------------------ 5xx 服务器错误状态码 (Server Error) ------------------------------
    # 表示服务器在处理请求的过程中有错误或者异常状态发生
    INTERNAL_SERVER_ERROR: Final[Dict[str, object]] = {
        "code": 500,
        "name": "Internal Server Error",
        "message": "服务器内部错误，无法完成请求"
    }

    NOT_IMPLEMENTED: Final[Dict[str, object]] = {
        "code": 501,
        "name": "Not Implemented",
        "message": "尚未实施"
    }

    BAD_GATEWAY: Final[Dict[str, object]] = {
        "code": 502,
        "name": "Bad Gateway",
        "message": "错误网关"
    }

    SERVICE_UNAVAILABLE: Final[Dict[str, object]] = {
        "code": 503,
        "name": "Service Unavailable",
        "message": "服务器当前无法处理请求"
    }

    GATEWAY_TIMEOUT: Final[Dict[str, object]] = {
        "code": 504,
        "name": "Gateway Timeout",
        "message": "网关超时"
    }

    HTTP_VERSION_NOT_SUPPORTED: Final[Dict[str, object]] = {
        "code": 505,
        "name": "HTTP Version Not Supported",
        "message": "不支持的HTTP版本"
    }

    VARIANT_ALSO_NEGOTIATES: Final[Dict[str, object]] = {
        "code": 506,
        "name": "Variant Also Negotiates",
        "message": "变体也在协商"
    }

    INSUFFICIENT_STORAGE: Final[Dict[str, object]] = {
        "code": 507,
        "name": "Insufficient Storage",
        "message": "服务器无法完成请求"
    }

    LOOP_DETECTED: Final[Dict[str, object]] = {
        "code": 508,
        "name": "Loop Detected",
        "message": "检测到循环"
    }

    NOT_EXTENDED: Final[Dict[str, object]] = {
        "code": 510,
        "name": "Not Extended",
        "message": "未扩展"
    }

    NETWORK_AUTHENTICATION_REQUIRED: Final[Dict[str, object]] = {
        "code": 511,
        "name": "Network Authentication Required",
        "message": "需要网络认证"
    }

    UNKNOWN: Final[Dict[str, object]] = {
        "code": 0,
        "name": "Unknown",
        "message": "未知错误"
    }