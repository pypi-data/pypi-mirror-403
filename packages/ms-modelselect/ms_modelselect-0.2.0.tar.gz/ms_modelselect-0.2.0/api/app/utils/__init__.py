# -*- coding: utf-8 -*-
"""工具模块"""

from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    hash_api_key,
)
from .deps import (
    get_current_user,
    get_current_tenant,
    get_current_active_user,
    require_admin,
    verify_api_key,
)
from .permissions import (
    permission_checker,
    require_permission,
    require_any_permission,
    require_resource_ownership,
    grant_role_to_user,
    revoke_role_from_user,
    get_user_roles,
)

__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "generate_api_key",
    "hash_api_key",
    "get_current_user",
    "get_current_tenant",
    "get_current_active_user",
    "require_admin",
    "verify_api_key",
    "permission_checker",
    "require_permission",
    "require_any_permission",
    "require_resource_ownership",
    "grant_role_to_user",
    "revoke_role_from_user",
    "get_user_roles",
]
