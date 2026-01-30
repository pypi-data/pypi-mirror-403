"""
数据模型定义

用于表示 API 响应数据的类。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class OemQuotaInfo:
    """OEM 单位额度信息

    Attributes:
        oem_name: OEM 单位名称
        activation_code_quota: 激活码总额度
        used_quota: 已使用额度
        remaining_quota: 剩余额度
    """

    oem_name: str
    activation_code_quota: int
    used_quota: int
    remaining_quota: int

    @classmethod
    def from_dict(cls, data: dict) -> "OemQuotaInfo":
        """从字典创建实例

        Args:
            data: API 响应数据字典

        Returns:
            OemQuotaInfo 实例
        """
        return cls(
            oem_name=data["oem_name"],
            activation_code_quota=data["activation_code_quota"],
            used_quota=data["used_quota"],
            remaining_quota=data["remaining_quota"],
        )

    def __str__(self) -> str:
        return (
            f"OEM单位: {self.oem_name}\n"
            f"总额度: {self.activation_code_quota}\n"
            f"已使用: {self.used_quota}\n"
            f"剩余: {self.remaining_quota}"
        )


@dataclass
class ActivationCodeInfo:
    """激活码信息

    Attributes:
        code: 激活码（UUID 字符串）
        validity_years: 有效期年限
        status: 状态 (0=未激活, 1=已激活, 2=已作废)
        activated_at: 激活时间（可能为 None）
        revoked_at: 作废时间（可能为 None）
        created_at: 创建时间
    """

    code: str
    validity_years: int
    status: int
    activated_at: datetime = None
    revoked_at: datetime = None
    created_at: datetime = None

    @property
    def status_display(self) -> str:
        """获取状态的中文显示"""
        status_map = {0: "未激活", 1: "已激活", 2: "已作废"}
        return status_map.get(self.status, "未知")

    @property
    def is_activated(self) -> bool:
        """是否已激活"""
        return self.status == 1

    @property
    def is_revoked(self) -> bool:
        """是否已作废"""
        return self.status == 2

    def __str__(self) -> str:
        return (
            f"激活码: {self.code}\n"
            f"有效期: {self.validity_years}年\n"
            f"状态: {self.status_display}"
        )


@dataclass
class GenerateCodesResult:
    """生成激活码结果

    Attributes:
        codes: 生成的激活码列表
        used_quota: 已使用额度
        remaining_quota: 剩余额度
        validity_years: 有效期年限
    """

    codes: List[str]
    used_quota: int
    remaining_quota: int
    validity_years: int

    @classmethod
    def from_dict(cls, data: dict, validity_years: int) -> "GenerateCodesResult":
        """从字典创建实例

        Args:
            data: API 响应数据字典
            validity_years: 有效期年限

        Returns:
            GenerateCodesResult 实例
        """
        return cls(
            codes=data["codes"],
            used_quota=data["used_quota"],
            remaining_quota=data["remaining_quota"],
            validity_years=validity_years,
        )

    def __str__(self) -> str:
        return (
            f"成功生成 {len(self.codes)} 个 {self.validity_years} 年期激活码\n"
            f"已使用额度: {self.used_quota}\n"
            f"剩余额度: {self.remaining_quota}"
        )


@dataclass
class RevokeCodeResult:
    """作废激活码结果

    Attributes:
        code: 被作废的激活码
        validity_years: 有效期年限
        revoked_at: 作废时间
        quota_restored: 额度是否已恢复
    """

    code: str
    validity_years: int
    revoked_at: datetime
    quota_restored: bool

    @classmethod
    def from_dict(cls, data: dict) -> "RevokeCodeResult":
        """从字典创建实例

        Args:
            data: API 响应数据字典

        Returns:
            RevokeCodeResult 实例
        """
        from datetime import datetime

        return cls(
            code=data["code"],
            validity_years=data["validity_years"],
            revoked_at=datetime.fromisoformat(data["revoked_at"]),
            quota_restored=data.get("quota_restored", False),
        )

    def __str__(self) -> str:
        quota_info = f"，已恢复 {self.validity_years} 年额度" if self.quota_restored else ""
        return f"成功作废激活码 {self.code}{quota_info}\n作废时间: {self.revoked_at}"


@dataclass
class ActivateCodeResult:
    """激活激活码结果

    Attributes:
        validity_years: 有效期年限
        activated_at: 激活时间
        oem_name: OEM 单位名称
    """

    validity_years: int
    activated_at: datetime
    oem_name: str

    @classmethod
    def from_dict(cls, data: dict) -> "ActivateCodeResult":
        """从字典创建实例

        Args:
            data: API 响应数据字典

        Returns:
            ActivateCodeResult 实例
        """
        from datetime import datetime

        return cls(
            validity_years=data["validity_years"],
            activated_at=datetime.fromisoformat(data["activated_at"]),
            oem_name=data["oem_name"],
        )

    def __str__(self) -> str:
        return (
            f"成功激活 {self.validity_years} 年期会员\n"
            f"OEM单位: {self.oem_name}\n"
            f"激活时间: {self.activated_at}"
        )


# ============ 管理 API 数据模型 ============


@dataclass
class BooksCountResult:
    """电子书总数结果"""

    count: int

    @classmethod
    def from_dict(cls, data: dict) -> "BooksCountResult":
        return cls(count=data["count"])

    def __str__(self) -> str:
        return f"电子书总数: {self.count}"


@dataclass
class UsersCountResult:
    """用户总数结果"""

    count: int

    @classmethod
    def from_dict(cls, data: dict) -> "UsersCountResult":
        return cls(count=data["count"])

    def __str__(self) -> str:
        return f"用户总数: {self.count}"


@dataclass
class MembersCountResult:
    """会员总数结果"""

    count: int

    @classmethod
    def from_dict(cls, data: dict) -> "MembersCountResult":
        return cls(count=data["count"])

    def __str__(self) -> str:
        return f"会员总数: {self.count}"


@dataclass
class BlockedBooksCountResult:
    """被屏蔽电子书总数结果"""

    count: int

    @classmethod
    def from_dict(cls, data: dict) -> "BlockedBooksCountResult":
        return cls(count=data["count"])

    def __str__(self) -> str:
        return f"被屏蔽电子书总数: {self.count}"


@dataclass
class RecentBooksCountResult:
    """最近一周新增电子书总数结果"""

    count: int

    @classmethod
    def from_dict(cls, data: dict) -> "RecentBooksCountResult":
        return cls(count=data["count"])

    def __str__(self) -> str:
        return f"最近一周新增电子书: {self.count}"


@dataclass
class RecentUsersCountResult:
    """最近一周新增用户总数结果"""

    count: int

    @classmethod
    def from_dict(cls, data: dict) -> "RecentUsersCountResult":
        return cls(count=data["count"])

    def __str__(self) -> str:
        return f"最近一周新增用户: {self.count}"


@dataclass
class RecentMembersCountResult:
    """最近一周新增会员总数结果"""

    count: int

    @classmethod
    def from_dict(cls, data: dict) -> "RecentMembersCountResult":
        return cls(count=data["count"])

    def __str__(self) -> str:
        return f"最近一周新增会员: {self.count}"


@dataclass
class SalesAmountResult:
    """总销售额结果"""

    total_amount: float

    @classmethod
    def from_dict(cls, data: dict) -> "SalesAmountResult":
        return cls(total_amount=data["total_amount"])

    def __str__(self) -> str:
        return f"总销售额: {self.total_amount}"


@dataclass
class SalesCountResult:
    """总销售量结果"""

    count: int

    @classmethod
    def from_dict(cls, data: dict) -> "SalesCountResult":
        return cls(count=data["count"])

    def __str__(self) -> str:
        return f"总销售量: {self.count}"


@dataclass
class UserInfo:
    """用户信息

    Attributes:
        id: 用户ID
        username: 用户名
        email: 邮箱
        phone: 电话
        balance: 余额
        is_member: 是否为会员
        is_banned: 是否被封禁
        created_at: 创建时间
    """

    id: int
    username: str
    email: str
    phone: str
    balance: float
    is_member: bool
    is_banned: bool
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "UserInfo":
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        return cls(
            id=data["id"],
            username=data["username"],
            email=data["email"],
            phone=data["phone"],
            balance=data.get("balance", 0.0),
            is_member=data.get("is_member", False),
            is_banned=data.get("is_banned", False),
            created_at=created_at,
        )

    def __str__(self) -> str:
        return (
            f"用户ID: {self.id}\n"
            f"用户名: {self.username}\n"
            f"邮箱: {self.email}\n"
            f"电话: {self.phone}\n"
            f"余额: {self.balance}\n"
            f"会员: {'是' if self.is_member else '否'}\n"
            f"封禁: {'是' if self.is_banned else '否'}"
        )


@dataclass
class AddUserResult:
    """添加用户结果"""

    user_id: int
    username: str

    @classmethod
    def from_dict(cls, data: dict) -> "AddUserResult":
        return cls(user_id=data["user_id"], username=data["username"])

    def __str__(self) -> str:
        return f"成功添加用户: {self.username} (ID: {self.user_id})"


@dataclass
class BanUserResult:
    """封禁用户结果"""

    user_id: int
    banned: bool

    @classmethod
    def from_dict(cls, data: dict) -> "BanUserResult":
        return cls(user_id=data["user_id"], banned=data["banned"])

    def __str__(self) -> str:
        status = "已封禁" if self.banned else "封禁失败"
        return f"用户 {self.user_id}: {status}"


@dataclass
class RechargeResult:
    """充值结果"""

    user_id: int
    amount: float
    balance: float

    @classmethod
    def from_dict(cls, data: dict) -> "RechargeResult":
        return cls(
            user_id=data["user_id"],
            amount=data["amount"],
            balance=data["balance"],
        )

    def __str__(self) -> str:
        return f"用户 {self.user_id} 充值 {self.amount}，余额: {self.balance}"


@dataclass
class DeductResult:
    """扣款结果"""

    user_id: int
    amount: float
    balance: float

    @classmethod
    def from_dict(cls, data: dict) -> "DeductResult":
        return cls(
            user_id=data["user_id"],
            amount=data["amount"],
            balance=data["balance"],
        )

    def __str__(self) -> str:
        return f"用户 {self.user_id} 扣款 {self.amount}，余额: {self.balance}"


@dataclass
class AddCategoryResult:
    """添加分类结果"""

    category_id: int
    name: str

    @classmethod
    def from_dict(cls, data: dict) -> "AddCategoryResult":
        return cls(category_id=data["category_id"], name=data["name"])

    def __str__(self) -> str:
        return f"成功添加分类: {self.name} (ID: {self.category_id})"


@dataclass
class BlockCommentResult:
    """屏蔽评论结果"""

    comment_id: int
    blocked: bool

    @classmethod
    def from_dict(cls, data: dict) -> "BlockCommentResult":
        return cls(comment_id=data["comment_id"], blocked=data["blocked"])

    def __str__(self) -> str:
        status = "已屏蔽" if self.blocked else "屏蔽失败"
        return f"评论 {self.comment_id}: {status}"


@dataclass
class BlockEbookResult:
    """屏蔽电子书结果"""

    ebook_id: int
    blocked: bool

    @classmethod
    def from_dict(cls, data: dict) -> "BlockEbookResult":
        return cls(ebook_id=data["ebook_id"], blocked=data["blocked"])

    def __str__(self) -> str:
        status = "已屏蔽" if self.blocked else "屏蔽失败"
        return f"电子书 {self.ebook_id}: {status}"


@dataclass
class DisableMfaResult:
    """禁用MFA结果"""

    user_id: int
    mfa_disabled: bool

    @classmethod
    def from_dict(cls, data: dict) -> "DisableMfaResult":
        return cls(user_id=data["user_id"], mfa_disabled=data["mfa_disabled"])

    def __str__(self) -> str:
        status = "已禁用" if self.mfa_disabled else "禁用失败"
        return f"用户 {self.user_id} MFA: {status}"