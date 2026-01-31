# -*- coding: utf-8 -*-
"""权限相关模型"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Permission(Base):
    """权限模型"""

    __tablename__ = "permissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="权限ID")
    code = Column(String(100), nullable=False, unique=True, comment="权限代码")
    name = Column(String(100), nullable=False, comment="权限名称")
    description = Column(Text, nullable=True, comment="权限描述")
    resource = Column(String(50), nullable=False, comment="资源类型")
    action = Column(String(50), nullable=False, comment="操作类型")
    category = Column(String(50), nullable=True, comment="权限分类")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    # 关系
    role_permissions = relationship("RolePermission", back_populates="permission")


class RolePermission(Base):
    """角色权限关联模型"""

    __tablename__ = "role_permissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    role = Column(String(50), nullable=False, comment="角色名称")
    permission_id = Column(BigInteger, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, comment="权限ID")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    # 关系
    permission = relationship("Permission", back_populates="role_permissions")


class UserRole(Base):
    """用户角色模型（支持多角色）"""

    __tablename__ = "user_roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    role = Column(String(50), nullable=False, comment="角色名称")
    granted_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="授权人ID")
    granted_at = Column(DateTime, nullable=False, default=datetime.now, comment="授权时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
