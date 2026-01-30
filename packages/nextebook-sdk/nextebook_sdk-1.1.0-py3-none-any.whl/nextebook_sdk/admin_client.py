"""
管理 API 客户端

用于与 NextEbook 管理 API 进行交互的客户端类。
"""

from typing import Optional
import requests

from .exceptions import (
    ManagementApiError,
    UserNotFoundError,
    InvalidParameterError,
    OperationFailedError,
    NetworkError,
    InvalidResponseError,
)
from .models import (
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


class AdminClient:
    """NextEbook 管理 API 客户端

    用于与 NextEbook 管理 API 进行交互，提供数据查询和系统管理功能。

    Example:
        >>> from nextebook_sdk import AdminClient
        >>>
        >>> # 初始化客户端
        >>> client = AdminClient(
        ...     base_url="http://127.0.0.1:9999",
        ...     api_key="your-api-key",
        ...     username="admin"
        ... )
        >>>
        >>> # 数据查询
        >>> books_count = client.get_books_count()
        >>> print(books_count)
        >>>
        >>> # 用户管理
        >>> user_info = client.get_user(user_id=123)
        >>> client.ban_user(user_id=123)
    """

    def __init__(self, base_url: str, api_key: str, username: str, timeout: int = 30):
        """初始化管理 API 客户端

        Args:
            base_url: API 基础 URL（如：http://127.0.0.1:9999）
            api_key: 管理 API 密钥
            username: 用户名
            timeout: 请求超时时间（秒），默认 30 秒
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.username = username
        self.timeout = timeout

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        params: dict = None,
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
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-Username": self.username,
        }

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
            ManagementApiError: 根据 API 错误码抛出相应的异常
        """
        if response_data.get("status") != "error":
            return

        message = response_data.get("message", "未知错误")

        # 根据常见错误消息映射到异常类型
        error_mapping = {
            "用户不存在": UserNotFoundError,
            "参数无效": InvalidParameterError,
            "操作失败": OperationFailedError,
        }

        # 尝试匹配错误类型
        for error_msg, error_class in error_mapping.items():
            if error_msg in message:
                raise error_class(message)

        # 默认抛出基础异常
        raise ManagementApiError(message)

    # ============ 数据查询方法 ============

    def get_books_count(self) -> int:
        """查询电子书总数

        Returns:
            电子书总数

        Raises:
            NetworkError: 网络请求失败
            InvalidResponseError: API 响应无效

        Example:
            >>> count = client.get_books_count()
            >>> print(f"电子书总数: {count}")
        """
        response_data = self._make_request("GET", "/api/data/books/count/")
        self._handle_error_response(response_data)
        return response_data.get("data", {}).get("count", 0)

    def get_users_count(self) -> int:
        """查询用户总数

        Returns:
            用户总数

        Raises:
            NetworkError: 网络请求失败
            InvalidResponseError: API 响应无效

        Example:
            >>> count = client.get_users_count()
            >>> print(f"用户总数: {count}")
        """
        response_data = self._make_request("GET", "/api/data/users/count/")
        self._handle_error_response(response_data)
        return response_data.get("data", {}).get("count", 0)

    def get_blocked_books_count(self) -> int:
        """查询被屏蔽的电子书总数

        Returns:
            被屏蔽的电子书总数

        Raises:
            NetworkError: 网络请求失败
            InvalidResponseError: API 响应无效

        Example:
            >>> count = client.get_blocked_books_count()
            >>> print(f"被屏蔽电子书总数: {count}")
        """
        response_data = self._make_request("GET", "/api/data/blocked-books/count/")
        self._handle_error_response(response_data)
        return response_data.get("data", {}).get("count", 0)

    def get_members_count(self) -> int:
        """查询会员总数

        Returns:
            会员总数

        Raises:
            NetworkError: 网络请求失败
            InvalidResponseError: API 响应无效

        Example:
            >>> count = client.get_members_count()
            >>> print(f"会员总数: {count}")
        """
        response_data = self._make_request("GET", "/api/data/members/count/")
        self._handle_error_response(response_data)
        return response_data.get("data", {}).get("count", 0)

    def get_recent_books_count(self) -> int:
        """查询最近一周新增的电子书总数

        Returns:
            最近一周新增的电子书总数

        Raises:
            NetworkError: 网络请求失败
            InvalidResponseError: API 响应无效

        Example:
            >>> count = client.get_recent_books_count()
            >>> print(f"最近一周新增电子书: {count}")
        """
        response_data = self._make_request("GET", "/api/data/recent/books/count/")
        self._handle_error_response(response_data)
        return response_data.get("data", {}).get("count", 0)

    def get_recent_users_count(self) -> int:
        """查询最近一周新增的用户总数

        Returns:
            最近一周新增的用户总数

        Raises:
            NetworkError: 网络请求失败
            InvalidResponseError: API 响应无效

        Example:
            >>> count = client.get_recent_users_count()
            >>> print(f"最近一周新增用户: {count}")
        """
        response_data = self._make_request("GET", "/api/data/recent/users/count/")
        self._handle_error_response(response_data)
        return response_data.get("data", {}).get("count", 0)

    def get_recent_members_count(self) -> int:
        """查询最近一周新增的会员总数

        Returns:
            最近一周新增的会员总数

        Raises:
            NetworkError: 网络请求失败
            InvalidResponseError: API 响应无效

        Example:
            >>> count = client.get_recent_members_count()
            >>> print(f"最近一周新增会员: {count}")
        """
        response_data = self._make_request("GET", "/api/data/recent/members/count/")
        self._handle_error_response(response_data)
        return response_data.get("data", {}).get("count", 0)

    def get_sales_amount(self) -> float:
        """查询总销售额

        Returns:
            总销售额

        Raises:
            NetworkError: 网络请求失败
            InvalidResponseError: API 响应无效

        Example:
            >>> amount = client.get_sales_amount()
            >>> print(f"总销售额: {amount}")
        """
        response_data = self._make_request("GET", "/api/data/sales/amount/")
        self._handle_error_response(response_data)
        return response_data.get("data", {}).get("total_amount", 0.0)

    def get_sales_count(self) -> int:
        """查询总销售量

        Returns:
            总销售量

        Raises:
            NetworkError: 网络请求失败
            InvalidResponseError: API 响应无效

        Example:
            >>> count = client.get_sales_count()
            >>> print(f"总销售量: {count}")
        """
        response_data = self._make_request("GET", "/api/data/sales/count/")
        self._handle_error_response(response_data)
        return response_data.get("data", {}).get("count", 0)

    # ============ 用户管理方法 ============

    def add_user(
        self, username: str, email: str, phone: str, password: str
    ) -> AddUserResult:
        """添加用户

        Args:
            username: 用户名
            email: 邮箱
            phone: 电话
            password: 密码

        Returns:
            AddUserResult: 添加用户结果对象

        Raises:
            InvalidParameterError: 参数无效
            OperationFailedError: 操作失败
            NetworkError: 网络请求失败

        Example:
            >>> result = client.add_user(
            ...     username="testuser",
            ...     email="test@example.com",
            ...     phone="13800138000",
            ...     password="password123"
            ... )
            >>> print(f"用户ID: {result.user_id}")
        """
        payload = {
            "username": username,
            "email": email,
            "phone": phone,
            "password": password,
        }

        response_data = self._make_request("POST", "/api/manage/user/add/", data=payload)
        self._handle_error_response(response_data)

        return AddUserResult.from_dict(response_data["data"])

    def get_user(self, user_id: int) -> UserInfo:
        """查询指定用户信息

        Args:
            user_id: 用户ID

        Returns:
            UserInfo: 用户信息对象

        Raises:
            UserNotFoundError: 用户不存在
            NetworkError: 网络请求失败

        Example:
            >>> user_info = client.get_user(user_id=123)
            >>> print(f"用户名: {user_info.username}")
        """
        response_data = self._make_request("GET", f"/api/manage/user/{user_id}/")
        self._handle_error_response(response_data)

        return UserInfo.from_dict(response_data["data"])

    def ban_user(self, user_id: int) -> BanUserResult:
        """封禁指定用户

        Args:
            user_id: 用户ID

        Returns:
            BanUserResult: 封禁用户结果对象

        Raises:
            UserNotFoundError: 用户不存在
            OperationFailedError: 操作失败
            NetworkError: 网络请求失败

        Example:
            >>> result = client.ban_user(user_id=123)
            >>> print(f"封禁状态: {result.banned}")
        """
        response_data = self._make_request("POST", f"/api/manage/user/{user_id}/ban/")
        self._handle_error_response(response_data)

        return BanUserResult.from_dict(response_data["data"])

    def recharge_user(self, user_id: int, amount: float) -> RechargeResult:
        """为指定用户充值

        Args:
            user_id: 用户ID
            amount: 充值金额

        Returns:
            RechargeResult: 充值结果对象

        Raises:
            UserNotFoundError: 用户不存在
            InvalidParameterError: 参数无效
            OperationFailedError: 操作失败
            NetworkError: 网络请求失败

        Example:
            >>> result = client.recharge_user(user_id=123, amount=100.0)
            >>> print(f"余额: {result.balance}")
        """
        payload = {"amount": amount}
        response_data = self._make_request(
            "POST", f"/api/manage/user/{user_id}/recharge/", data=payload
        )
        self._handle_error_response(response_data)

        return RechargeResult.from_dict(response_data["data"])

    def deduct_user(self, user_id: int, amount: float) -> DeductResult:
        """为指定用户扣款

        Args:
            user_id: 用户ID
            amount: 扣款金额

        Returns:
            DeductResult: 扣款结果对象

        Raises:
            UserNotFoundError: 用户不存在
            InvalidParameterError: 参数无效
            OperationFailedError: 操作失败
            NetworkError: 网络请求失败

        Example:
            >>> result = client.deduct_user(user_id=123, amount=50.0)
            >>> print(f"余额: {result.balance}")
        """
        payload = {"amount": amount}
        response_data = self._make_request(
            "POST", f"/api/manage/user/{user_id}/deduct/", data=payload
        )
        self._handle_error_response(response_data)

        return DeductResult.from_dict(response_data["data"])

    def disable_user_mfa(self, user_id: int) -> DisableMfaResult:
        """禁用指定用户的 MFA

        Args:
            user_id: 用户ID

        Returns:
            DisableMfaResult: 禁用MFA结果对象

        Raises:
            UserNotFoundError: 用户不存在
            OperationFailedError: 操作失败
            NetworkError: 网络请求失败

        Example:
            >>> result = client.disable_user_mfa(user_id=123)
            >>> print(f"MFA已禁用: {result.mfa_disabled}")
        """
        response_data = self._make_request("POST", f"/api/manage/user/{user_id}/mfa/disable/")
        self._handle_error_response(response_data)

        return DisableMfaResult.from_dict(response_data["data"])

    # ============ 分类管理方法 ============

    def add_category(
        self, name: str, creator_id: int, description: str = None
    ) -> AddCategoryResult:
        """添加分类

        Args:
            name: 分类名称
            creator_id: 创建者ID
            description: 分类描述（可选）

        Returns:
            AddCategoryResult: 添加分类结果对象

        Raises:
            InvalidParameterError: 参数无效
            OperationFailedError: 操作失败
            NetworkError: 网络请求失败

        Example:
            >>> result = client.add_category(
            ...     name="小说",
            ...     creator_id=1,
            ...     description="各类小说作品"
            ... )
            >>> print(f"分类ID: {result.category_id}")
        """
        payload = {"name": name, "creator_id": creator_id}
        if description:
            payload["description"] = description

        response_data = self._make_request("POST", "/api/manage/category/add/", data=payload)
        self._handle_error_response(response_data)

        return AddCategoryResult.from_dict(response_data["data"])

    # ============ 内容管理方法 ============

    def block_comment(self, comment_id: int) -> BlockCommentResult:
        """屏蔽指定评论

        Args:
            comment_id: 评论ID

        Returns:
            BlockCommentResult: 屏蔽评论结果对象

        Raises:
            OperationFailedError: 操作失败
            NetworkError: 网络请求失败

        Example:
            >>> result = client.block_comment(comment_id=456)
            >>> print(f"已屏蔽: {result.blocked}")
        """
        response_data = self._make_request("POST", f"/api/manage/comment/{comment_id}/block/")
        self._handle_error_response(response_data)

        return BlockCommentResult.from_dict(response_data["data"])

    def block_ebook(self, ebook_id: int) -> BlockEbookResult:
        """屏蔽指定电子书

        Args:
            ebook_id: 电子书ID

        Returns:
            BlockEbookResult: 屏蔽电子书结果对象

        Raises:
            OperationFailedError: 操作失败
            NetworkError: 网络请求失败

        Example:
            >>> result = client.block_ebook(ebook_id=789)
            >>> print(f"已屏蔽: {result.blocked}")
        """
        response_data = self._make_request("POST", f"/api/manage/ebook/{ebook_id}/block/")
        self._handle_error_response(response_data)

        return BlockEbookResult.from_dict(response_data["data"])

    def __repr__(self) -> str:
        """返回客户端的字符串表示"""
        return f"AdminClient(base_url='{self.base_url}', username='{self.username}')"
