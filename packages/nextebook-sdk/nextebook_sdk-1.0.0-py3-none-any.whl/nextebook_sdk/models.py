"""
数据模型定义

用于表示 API 响应数据的类。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List


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