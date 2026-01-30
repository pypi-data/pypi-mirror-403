"""
NextEbook SDK 异常类定义

所有 SDK 异常的基类和特定异常类型。
"""


class NextEbookApiError(Exception):
    """NextEbook API 基础异常类

    所有 NextEbook SDK 相关异常的父类。

    Attributes:
        message: 错误消息
        status_code: HTTP 状态码（如果可用）
    """

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class OemApiError(NextEbookApiError):
    """OEM API 基础异常类

    所有 OEM API 相关异常的父类。
    """

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message, status_code)


class InvalidApiKeyError(OemApiError):
    """无效的 API 密钥

    当提供的 API 密钥不存在或格式错误时抛出。
    """

    def __init__(self, message: str = "无效的API密钥"):
        super().__init__(message, status_code=401)


class InsufficientQuotaError(OemApiError):
    """额度不足

    当 OEM 单位的剩余额度不足以生成请求的激活码时抛出。
    """

    def __init__(self, message: str = "额度不足"):
        super().__init__(message, status_code=403)


class InvalidCodeError(OemApiError):
    """无效的激活码

    当提供的激活码不存在或格式错误时抛出。
    """

    def __init__(self, message: str = "无效的激活码"):
        super().__init__(message, status_code=404)


class AlreadyActivatedError(OemApiError):
    """激活码已被激活

    当尝试使用已被激活的激活码时抛出。
    """

    def __init__(self, message: str = "激活码已被激活"):
        super().__init__(message, status_code=403)


class CannotRevokeActivatedError(OemApiError):
    """无法作废已激活的激活码

    当尝试作废已激活的激活码时抛出（已激活的激活码不可作废）。
    """

    def __init__(self, message: str = "已激活的激活码不可作废"):
        super().__init__(message, status_code=403)


class PermissionDeniedError(OemApiError):
    """权限不足

    当 OEM 单位尝试操作不属于它的激活码时抛出。
    """

    def __init__(self, message: str = "权限不足"):
        super().__init__(message, status_code=403)


class AlreadyRevokedError(OemApiError):
    """激活码已作废

    当尝试作废已作废的激活码时抛出。
    """

    def __init__(self, message: str = "激活码已作废"):
        super().__init__(message, status_code=400)


class NetworkError(NextEbookApiError):
    """网络错误

    当网络请求失败时抛出。
    """

    def __init__(self, message: str = "网络请求失败"):
        super().__init__(message)


class InvalidResponseError(NextEbookApiError):
    """无效的响应

    当 API 返回的响应格式无效时抛出。
    """

    def __init__(self, message: str = "无效的API响应"):
        super().__init__(message)


# ============ 管理 API 异常类 ============


class ManagementApiError(NextEbookApiError):
    """管理 API 基础异常类

    所有管理 API 相关异常的父类。
    """

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message, status_code)


class UserNotFoundError(ManagementApiError):
    """用户不存在

    当尝试查询或操作不存在的用户时抛出。
    """

    def __init__(self, message: str = "用户不存在"):
        super().__init__(message, status_code=404)


class InvalidParameterError(ManagementApiError):
    """参数无效

    当提供的参数不满足要求时抛出。
    """

    def __init__(self, message: str = "参数无效"):
        super().__init__(message, status_code=400)


class OperationFailedError(ManagementApiError):
    """操作失败

    当管理操作执行失败时抛出。
    """

    def __init__(self, message: str = "操作失败"):
        super().__init__(message, status_code=500)
