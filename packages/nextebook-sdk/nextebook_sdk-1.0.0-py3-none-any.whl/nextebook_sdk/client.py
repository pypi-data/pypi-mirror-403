"""
OEM API 客户端

用于与 NextEbook OEM API 进行交互的客户端类。
"""

import uuid
from typing import List, Optional
import requests

from .exceptions import (
    OemApiError,
    InvalidApiKeyError,
    InsufficientQuotaError,
    InvalidCodeError,
    AlreadyActivatedError,
    CannotRevokeActivatedError,
    PermissionDeniedError,
    AlreadyRevokedError,
    NetworkError,
    InvalidResponseError,
)
from .models import OemQuotaInfo, GenerateCodesResult, RevokeCodeResult, ActivateCodeResult


class OemClient:
    """NextEbook OEM API 客户端

    用于与 NextEbook OEM API 进行交互，提供激活码生成、查询、作废等功能。

    Example:
        >>> from nextebook_sdk import OemClient
        >>>
        >>> # 初始化客户端
        >>> client = OemClient(
        ...     base_url="http://127.0.0.1:9999",
        ...     api_key="3d0a7dc8-796f-4206-9bc2-b313e6c92a29"
        ... )
        >>>
        >>> # 检查额度
        >>> quota = client.check_quota()
        >>> print(quota.remaining_quota)
        >>>
        >>> # 生成激活码
        >>> result = client.generate_codes(count=10, validity_years=1)
        >>> print(result.codes)
        >>>
        >>> # 作废激活码
        >>> result = client.revoke_code(code="xxx")
    """

    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        """初始化 OEM API 客户端

        Args:
            base_url: API 基础 URL（如：http://127.0.0.1:9999）
            api_key: OEM API 密钥（UUID 格式字符串）
            timeout: 请求超时时间（秒），默认 30 秒

        Raises:
            ValueError: 如果 API 密钥不是有效的 UUID 格式
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # 验证 API 密钥格式
        try:
            self.api_key = str(uuid.UUID(api_key))
        except ValueError:
            raise ValueError(f"无效的 API 密钥格式: {api_key}")

    def _make_request(
        self, method: str, endpoint: str, data: dict = None, params: dict = None
    ) -> dict:
        """发起 HTTP 请求

        Args:
            method: HTTP 方法（GET/POST）
            endpoint: API 端点路径
            data: POST 请求的 JSON 数据
            params: GET 请求的查询参数

        Returns:
            API 响应的 JSON 数据

        Raises:
            NetworkError: 网络请求失败
            InvalidResponseError: API 响应无效
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            # 解析 JSON 响应
            try:
                response_data = response.json()
            except ValueError:
                raise InvalidResponseError(f"无法解析 JSON 响应: {response.text[:200]}")

            return response_data

        except requests.Timeout:
            raise NetworkError(f"请求超时（超过 {self.timeout} 秒）")
        except requests.ConnectionError as e:
            raise NetworkError(f"连接失败: {str(e)}")
        except requests.RequestException as e:
            raise NetworkError(f"网络请求失败: {str(e)}")

    def _handle_error_response(self, response_data: dict):
        """处理 API 错误响应

        Args:
            response_data: API 响应数据

        Raises:
            OemApiError: 根据 API 错误码抛出相应的异常
        """
        if response_data.get("status") != "error":
            return

        message = response_data.get("message", "未知错误")

        # 根据常见错误消息映射到异常类型
        error_mapping = {
            "无效的API密钥": InvalidApiKeyError,
            "额度不足": InsufficientQuotaError,
            "无效的激活码": InvalidCodeError,
            "激活码已被激活": AlreadyActivatedError,
            "已激活的激活码不可作废": CannotRevokeActivatedError,
            "权限不足": PermissionDeniedError,
            "激活码已作废": AlreadyRevokedError,
        }

        # 尝试匹配错误类型
        for error_msg, error_class in error_mapping.items():
            if error_msg in message:
                raise error_class(message)

        # 默认抛出基础异常
        raise OemApiError(message)

    def check_quota(self) -> OemQuotaInfo:
        """检查 OEM 单位的激活码额度

        Returns:
            OemQuotaInfo: 额度信息对象

        Raises:
            InvalidApiKeyError: API 密钥无效
            NetworkError: 网络请求失败

        Example:
            >>> quota = client.check_quota()
            >>> print(f"剩余额度: {quota.remaining_quota}")
        """
        response_data = self._make_request(
            "GET", "/oem-api/check-quota/", params={"api_key": self.api_key}
        )

        self._handle_error_response(response_data)

        return OemQuotaInfo.from_dict(response_data["data"])

    def generate_codes(self, count: int = 1, validity_years: int = 1) -> GenerateCodesResult:
        """生成激活码

        Args:
            count: 生成数量（1-100），默认 1
            validity_years: 有效期年限（1/2/3），默认 1

        Returns:
            GenerateCodesResult: 生成结果对象

        Raises:
            InvalidApiKeyError: API 密钥无效
            InsufficientQuotaError: 额度不足
            ValueError: 参数无效

        Example:
            >>> result = client.generate_codes(count=10, validity_years=2)
            >>> for code in result.codes:
            ...     print(code)
        """
        # 验证参数
        if count <= 0:
            raise ValueError("生成数量必须大于 0")
        if count > 100:
            raise ValueError("单次最多生成 100 个激活码")
        if validity_years not in [1, 2, 3]:
            raise ValueError("有效期年限必须是 1、2 或 3")

        payload = {"api_key": self.api_key, "count": count, "validity_years": validity_years}

        response_data = self._make_request("POST", "/oem-api/generate-codes/", data=payload)

        self._handle_error_response(response_data)

        return GenerateCodesResult.from_dict(response_data["data"], validity_years)

    def revoke_code(self, code: str) -> RevokeCodeResult:
        """作废激活码

        业务规则：
        - 只有未激活的激活码可以被作废
        - 已激活的激活码不可作废（已被用户使用）
        - 作废后额度会恢复
        - 被作废的激活码不可再激活

        Args:
            code: 要作废的激活码（UUID 字符串）

        Returns:
            RevokeCodeResult: 作废结果对象

        Raises:
            InvalidApiKeyError: API 密钥无效
            InvalidCodeError: 激活码无效
            CannotRevokeActivatedError: 激活码已激活，不可作废
            AlreadyRevokedError: 激活码已作废
            PermissionDeniedError: 无权操作该激活码

        Example:
            >>> result = client.revoke_code("550e8400-e29b-41d4-a716-446655440000")
            >>> print(f"额度恢复: {result.quota_restored}")
        """
        # 验证激活码格式
        try:
            code = str(uuid.UUID(code))
        except ValueError:
            raise ValueError(f"无效的激活码格式: {code}")

        payload = {"api_key": self.api_key, "code": code}

        response_data = self._make_request("POST", "/oem-api/revoke-code/", data=payload)

        self._handle_error_response(response_data)

        return RevokeCodeResult.from_dict(response_data["data"])

    def activate_code(self, code: str, user_id: int) -> ActivateCodeResult:
        """激活会员卡激活码

        Args:
            code: 激活码（UUID 字符串）
            user_id: 用户 ID

        Returns:
            ActivateCodeResult: 激活结果对象

        Raises:
            InvalidCodeError: 激活码无效
            AlreadyActivatedError: 激活码已被激活
            PermissionDeniedError: 无权操作该激活码

        Example:
            >>> result = client.activate_code("550e8400-e29b-41d4-a716-446655440000", user_id=123)
            >>> print(f"会员有效期: {result.validity_years} 年")
        """
        # 验证激活码格式
        try:
            code = str(uuid.UUID(code))
        except ValueError:
            raise ValueError(f"无效的激活码格式: {code}")

        payload = {"code": code, "user_id": user_id}

        response_data = self._make_request("POST", "/oem-api/activate-code/", data=payload)

        self._handle_error_response(response_data)

        return ActivateCodeResult.from_dict(response_data["data"])

    def __repr__(self) -> str:
        """返回客户端的字符串表示"""
        return f"OemClient(base_url='{self.base_url}', api_key='...{self.api_key[-8:]}')"