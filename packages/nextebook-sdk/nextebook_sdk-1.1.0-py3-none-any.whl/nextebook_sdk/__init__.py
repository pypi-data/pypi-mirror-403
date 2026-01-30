"""
NextEbook SDK

用于与 NextEbook API 进行交互的 Python SDK。

提供两个客户端:
- OemClient: 用于 OEM 激活码管理
- AdminClient: 用于数据查询和系统管理

主要功能:
OEM API:
- 检查 OEM 单位额度
- 生成会员卡激活码
- 作废激活码
- 激活会员卡

管理 API:
- 数据查询（电子书、用户、会员、销售统计）
- 用户管理（添加、查询、封禁、充值、扣款、禁用MFA）
- 分类管理
- 内容管理（屏蔽评论、电子书）
"""

__version__ = "1.1.0"
__author__ = "NextEbook Team"

# 客户端
from .client import OemClient
from .admin_client import AdminClient

# 异常类
from .exceptions import (
    NextEbookApiError,
    OemApiError,
    ManagementApiError,
    InvalidApiKeyError,
    InsufficientQuotaError,
    InvalidCodeError,
    AlreadyActivatedError,
    CannotRevokeActivatedError,
    PermissionDeniedError,
    AlreadyRevokedError,
    UserNotFoundError,
    InvalidParameterError,
    OperationFailedError,
    NetworkError,
    InvalidResponseError,
)

# 数据模型
from .models import (
    ActivationCodeInfo,
    OemQuotaInfo,
    GenerateCodesResult,
    RevokeCodeResult,
    ActivateCodeResult,
    BooksCountResult,
    UsersCountResult,
    MembersCountResult,
    BlockedBooksCountResult,
    RecentBooksCountResult,
    RecentUsersCountResult,
    RecentMembersCountResult,
    SalesAmountResult,
    SalesCountResult,
    UserInfo,
    AddUserResult,
    BanUserResult,
    RechargeResult,
    DeductResult,
    AddCategoryResult,
    BlockCommentResult,
    BlockEbookResult,
    DisableMfaResult,
)

__all__ = [
    # 版本
    "__version__",
    # 客户端
    "OemClient",
    "AdminClient",
    # 异常类
    "NextEbookApiError",
    "OemApiError",
    "ManagementApiError",
    "InvalidApiKeyError",
    "InsufficientQuotaError",
    "InvalidCodeError",
    "AlreadyActivatedError",
    "CannotRevokeActivatedError",
    "PermissionDeniedError",
    "AlreadyRevokedError",
    "UserNotFoundError",
    "InvalidParameterError",
    "OperationFailedError",
    "NetworkError",
    "InvalidResponseError",
    # OEM API 模型
    "ActivationCodeInfo",
    "OemQuotaInfo",
    "GenerateCodesResult",
    "RevokeCodeResult",
    "ActivateCodeResult",
    # 管理 API 模型
    "BooksCountResult",
    "UsersCountResult",
    "MembersCountResult",
    "BlockedBooksCountResult",
    "RecentBooksCountResult",
    "RecentUsersCountResult",
    "RecentMembersCountResult",
    "SalesAmountResult",
    "SalesCountResult",
    "UserInfo",
    "AddUserResult",
    "BanUserResult",
    "RechargeResult",
    "DeductResult",
    "AddCategoryResult",
    "BlockCommentResult",
    "BlockEbookResult",
    "DisableMfaResult",
]
