"""
FastAPI integration for GlobalAuth.
"""
from opengater_globalauth_client.fastapi.middleware import AuthMiddleware, USER_STATE_KEY
from opengater_globalauth_client.fastapi.dependencies import (
    get_current_user,
    get_current_user_optional,
    require_admin,
    require_verified,
)

__all__ = [
    "AuthMiddleware",
    "USER_STATE_KEY",
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
    "require_verified",
]
