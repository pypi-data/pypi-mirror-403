"""
NextEbook OEM SDK

用于与 NextEbook OEM API 进行交互的 Python SDK。

主要功能:
- 检查 OEM 单位额度
- 生成会员卡激活码
- 作废激活码
- 激活会员卡
"""

__version__ = "1.0.0"
__author__ = "NextEbook Team"

from .client import OemClient
from .exceptions import (
    OemApiError,
    InvalidApiKeyError,
    InsufficientQuotaError,
    InvalidCodeError,
    AlreadyActivatedError,
    CannotRevokeActivatedError,
    PermissionDeniedError,
    AlreadyRevokedError,
)
from .models import ActivationCodeInfo, OemQuotaInfo

__all__ = [
    "OemClient",
    "OemApiError",
    "InvalidApiKeyError",
    "InsufficientQuotaError",
    "InvalidCodeError",
    "AlreadyActivatedError",
    "CannotRevokeActivatedError",
    "PermissionDeniedError",
    "AlreadyRevokedError",
    "ActivationCodeInfo",
    "OemQuotaInfo",
    "__version__",
]