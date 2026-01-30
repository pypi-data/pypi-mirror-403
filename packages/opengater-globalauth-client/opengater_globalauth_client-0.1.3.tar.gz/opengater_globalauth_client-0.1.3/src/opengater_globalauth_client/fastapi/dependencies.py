"""
FastAPI dependencies for GlobalAuth.
"""
from typing import Callable

from fastapi import Request, HTTPException, Depends, Header

from opengater_globalauth_client.client import GlobalAuthClient
from opengater_globalauth_client.models import User
from opengater_globalauth_client.fastapi.middleware import USER_STATE_KEY
from opengater_globalauth_client.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    TokenInvalidError,
    UserBannedError,
)


def get_current_user(client: GlobalAuthClient | None = None) -> Callable:
    """
    Dependency factory for getting current authenticated user.
    
    Can be used in two ways:
    
    1. With AuthMiddleware (recommended):
        User is already validated by middleware, just extract from request.state.
        ```python
        @app.get("/me")
        async def me(user: User = Depends(get_current_user())):
            return user
        ```
    
    2. Without middleware (standalone):
        Pass client to validate token manually.
        ```python
        client = GlobalAuthClient(...)
        
        @app.get("/me")
        async def me(user: User = Depends(get_current_user(client))):
            return user
        ```
    
    Args:
        client: Optional GlobalAuthClient for standalone mode
    
    Returns:
        Dependency function that returns User
    """
    async def dependency(
        request: Request,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> User:
        # Try to get user from middleware first
        user = getattr(request.state, USER_STATE_KEY, None)
        
        if user is not None:
            return user
        
        # Standalone mode - validate token manually
        if client is None:
            raise HTTPException(
                status_code=500,
                detail="Auth middleware not configured and no client provided"
            )
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Authorization header required"
            )
        
        token = authorization[7:]
        
        try:
            return await client.introspect(token)
        
        except TokenExpiredError:
            raise HTTPException(status_code=401, detail="Token expired")
        
        except UserBannedError:
            raise HTTPException(status_code=403, detail="User is banned")
        
        except (TokenInvalidError, AuthenticationError):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        except Exception:
            raise HTTPException(status_code=503, detail="Auth service unavailable")
    
    return dependency


def get_current_user_optional(client: GlobalAuthClient | None = None) -> Callable:
    """
    Dependency for optionally getting current user.
    
    Returns None if no token provided, User if valid token.
    Raises exception only for invalid/expired tokens.
    
    Example:
        ```python
        @app.get("/items")
        async def list_items(user: User | None = Depends(get_current_user_optional())):
            if user:
                return {"items": [...], "user_id": user.id}
            return {"items": [...]}
        ```
    """
    async def dependency(
        request: Request,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> User | None:
        # Try to get user from middleware
        user = getattr(request.state, USER_STATE_KEY, None)
        
        if user is not None:
            return user
        
        # No token - that's ok for optional auth
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        # Has token - validate it
        if client is None:
            return None
        
        token = authorization[7:]
        
        try:
            return await client.introspect(token)
        
        except TokenExpiredError:
            raise HTTPException(status_code=401, detail="Token expired")
        
        except UserBannedError:
            raise HTTPException(status_code=403, detail="User is banned")
        
        except (TokenInvalidError, AuthenticationError):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        except Exception:
            # Service unavailable - treat as no auth for optional
            return None
    
    return dependency


def require_admin(client: GlobalAuthClient | None = None) -> Callable:
    """
    Dependency that requires admin user.
    
    Example:
        ```python
        @app.delete("/users/{user_id}")
        async def delete_user(
            user_id: str,
            admin: User = Depends(require_admin())
        ):
            # Only admins can access this
            ...
        ```
    """
    user_dependency = get_current_user(client)
    
    async def dependency(
        request: Request,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> User:
        user = await user_dependency(request, authorization)
        
        if not user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        
        return user
    
    return dependency


def require_verified(client: GlobalAuthClient | None = None) -> Callable:
    """
    Dependency that requires verified user.
    
    Example:
        ```python
        @app.post("/orders")
        async def create_order(
            user: User = Depends(require_verified())
        ):
            # Only verified users can create orders
            ...
        ```
    """
    user_dependency = get_current_user(client)
    
    async def dependency(
        request: Request,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> User:
        user = await user_dependency(request, authorization)
        
        if not user.verified:
            raise HTTPException(
                status_code=403,
                detail="Verified account required"
            )
        
        return user
    
    return dependency
