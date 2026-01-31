from typing import Dict, Final


# 控制器路径类型常量核心类（对应PHP的ControllerPathType）
class ControllerPathType:
    """
    控制器路径类型常量类
    定义系统中常用的接口路径、名称、标识键，统一管理控制器的标准化接口路径。

    字段说明:
    - path: 接口路径后缀
    - name: 接口功能中文名称
    - key: 接口功能唯一标识键
    - description: 接口详细描述（预留字段，原类为空）

    使用示例:
    ControllerPathType.DELETE["path"]        # "/delete"
    ControllerPathType.CREATE["name"]         # "创建"
    ControllerPathType.LISTS["key"]           # "list"
    """

    # ------------------------------ 基础操作类 ------------------------------
    DELETE: Final[Dict[str, str]] = {
        'path': '/delete',
        'name': '删除',
        'key': 'delete',
        'description': ''
    }

    REMOVE: Final[Dict[str, str]] = {
        'path': '/remove',
        'name': '删除',
        'key': 'remove',
        'description': ''
    }

    CREATE: Final[Dict[str, str]] = {
        'path': '/create',
        'name': '创建',
        'key': 'create',
        'description': ''
    }

    CREATE_BATCH: Final[Dict[str, str]] = {
        'path': '/create/batch',
        'name': '批量创建',
        'key': 'createBatch',
        'description': ''
    }

    ADD: Final[Dict[str, str]] = {
        'path': '/add',
        'name': '创建',
        'key': 'add',
        'description': ''
    }

    ADD_BATCH: Final[Dict[str, str]] = {
        'path': '/add/batch',
        'name': '批量创建',
        'key': 'addBatch',
        'description': ''
    }

    EDIT: Final[Dict[str, str]] = {
        'path': '/edit',
        'name': '更新',
        'key': 'edit',
        'description': ''
    }

    EDIT_BATCH: Final[Dict[str, str]] = {
        'path': '/edit/batch',
        'name': '批量更新',
        'key': 'editBatch',
        'description': ''
    }

    UPDATE: Final[Dict[str, str]] = {
        'path': '/update',
        'name': '更新',
        'key': 'update',
        'description': ''
    }

    SAVE: Final[Dict[str, str]] = {
        'path': '/save',
        'name': '保存',
        'key': 'save',
        'description': ''
    }

    # ------------------------------ 状态操作类 ------------------------------
    STATUS: Final[Dict[str, str]] = {
        'path': '/status',
        'name': '状态',
        'key': 'status',
        'description': ''
    }

    STATUS_UPDATE: Final[Dict[str, str]] = {
        'path': '/status/update',
        'name': '状态修改',
        'key': 'statusUpdate',
        'description': ''
    }

    STATUS_UPDATE_BATCH: Final[Dict[str, str]] = {
        'path': '/status/update/batch',
        'name': '状态批量修改',
        'key': 'statusUpdateBatch',
        'description': ''
    }

    # ------------------------------ 数据查询/展示类 ------------------------------
    LISTS: Final[Dict[str, str]] = {
        'path': '/list',
        'name': '列表',
        'key': 'list',
        'description': ''
    }

    LIST_SHOW: Final[Dict[str, str]] = {
        'path': '/list/show',
        'name': '列表',
        'key': 'listShow',
        'description': ''
    }

    DETAIL: Final[Dict[str, str]] = {
        'path': '/detail',
        'name': '详情',
        'key': 'detail',
        'description': ''
    }

    DETAIL_SHOW: Final[Dict[str, str]] = {
        'path': '/detail/show',
        'name': '详情',
        'key': 'detailShow',
        'description': ''
    }

    SELECT: Final[Dict[str, str]] = {
        'path': '/select',
        'name': '选择器',
        'key': 'select',
        'description': ''
    }

    TREE: Final[Dict[str, str]] = {
        'path': '/tree',
        'name': '树列表',
        'key': 'tree',
        'description': ''
    }

    INDEX: Final[Dict[str, str]] = {
        'path': '/index',
        'name': '视图',
        'key': 'index',
        'description': ''
    }

    # ------------------------------ 数据统计类 ------------------------------
    TOTAL: Final[Dict[str, str]] = {
        'path': '/total',
        'name': '总数',
        'key': 'total',
        'description': ''
    }

    SUM: Final[Dict[str, str]] = {
        'path': '/sum',
        'name': '统计',
        'key': 'sum',
        'description': ''
    }

    # ------------------------------ 导入/导出类 ------------------------------
    DOWNLOAD: Final[Dict[str, str]] = {
        'path': '/download',
        'name': '下载',
        'key': 'download',
        'description': ''
    }

    EXPORT: Final[Dict[str, str]] = {
        'path': '/export',
        'name': '导出',
        'key': 'export',
        'description': ''
    }

    EXPORT_EXCEL: Final[Dict[str, str]] = {
        'path': '/export/excel',
        'name': '导出Excel',
        'key': 'exportExcel',
        'description': ''
    }

    IMPORT: Final[Dict[str, str]] = {
        'path': '/import',
        'name': '导出',  # 保留原类字段值（疑似笔误）
        'key': 'import',
        'description': ''
    }

    IMPORT_EXCEL: Final[Dict[str, str]] = {
        'path': '/import/excel',
        'name': '导出Excel',  # 保留原类字段值（疑似笔误）
        'key': 'importExcel',
        'description': ''
    }

    # ------------------------------ 其他操作类 ------------------------------
    LOCK: Final[Dict[str, str]] = {
        'path': '/lock',
        'name': '锁',
        'key': 'lock',
        'description': ''
    }

    CACHE_CLEAR: Final[Dict[str, str]] = {
        'path': '/cache/clear',
        'name': '缓存清理',
        'key': 'cacheClear',
        'description': ''
    }

    TABLE: Final[Dict[str, str]] = {
        'path': '/table',
        'name': '表格',
        'key': 'table',
        'description': ''
    }

    # ------------------------------ 自定义操作类 ------------------------------
    SEARCH_CUSTOM: Final[Dict[str, str]] = {
        'path': '/search/custom',
        'name': '搜索自定义',
        'key': 'searchCustom',
        'description': ''
    }

    TABLE_CUSTOM: Final[Dict[str, str]] = {
        'path': '/table/custom',
        'name': '表格自定义',
        'key': 'tableCustom',
        'description': ''
    }

    CREATE_CUSTOM: Final[Dict[str, str]] = {
        'path': '/create/custom',
        'name': '创建自定义',
        'key': 'createCustom',
        'description': ''
    }

    UPDATE_CUSTOM: Final[Dict[str, str]] = {
        'path': '/update/custom',
        'name': '编辑自定义',
        'key': 'updateCustom',
        'description': ''
    }

    SAVE_CUSTOM: Final[Dict[str, str]] = {
        'path': '/save/custom',
        'name': '保存自定义',
        'key': 'saveCustom',
        'description': ''
    }

    # ------------------------------ 配置相关操作类 ------------------------------
    CONFIG_INDEX: Final[Dict[str, str]] = {
        'path': '/config/index',
        'name': '配置视图',
        'key': 'configIndex',
        'description': ''
    }

    CONFIG_LIST: Final[Dict[str, str]] = {
        'path': '/config/list',
        'name': '配置列表',
        'key': 'configList',
        'description': ''
    }

    CONFIG_CUSTOM: Final[Dict[str, str]] = {
        'path': '/config/custom',
        'name': '配置自定义',
        'key': 'configCustom',
        'description': ''
    }

    CONFIG_DETAIL: Final[Dict[str, str]] = {
        'path': '/config/detail',
        'name': '配置详情',
        'key': 'configDetail',
        'description': ''
    }

    CONFIG_CREATE: Final[Dict[str, str]] = {
        'path': '/config/create',
        'name': '配置添加',
        'key': 'configCreate',
        'description': ''
    }

    CONFIG_UPDATE: Final[Dict[str, str]] = {
        'path': '/config/update',
        'name': '配置修改',
        'key': 'configUpdate',
        'description': ''
    }

    CONFIG_SAVE: Final[Dict[str, str]] = {
        'path': '/config/save',
        'name': '配置保存',
        'key': 'configSave',
        'description': ''
    }