"""
FastAPI middleware for automatic token validation.
"""
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from opengater_globalauth_client.client import GlobalAuthClient
from opengater_globalauth_client.models import User
from opengater_globalauth_client.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    TokenInvalidError,
    UserBannedError,
    ConnectionError,
)


# Request state key for storing user
USER_STATE_KEY = "globalauth_user"


class AuthMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic token validation.
    
    Validates Bearer token from Authorization header and stores
    user in request.state for access in endpoints.
    
    Args:
        app: FastAPI application
        client: GlobalAuthClient instance
        exclude_paths: Paths to exclude from auth (default: /health, /docs, /openapi.json, /redoc)
        on_error: Optional custom error handler
    
    Example:
        ```python
        from fastapi import FastAPI
        from opengater_globalauth_client import GlobalAuthClient
        from opengater_globalauth_client.fastapi import AuthMiddleware
        
        app = FastAPI()
        client = GlobalAuthClient(base_url="...", service_slug="opengater")
        
        app.add_middleware(
            AuthMiddleware,
            client=client,
            exclude_paths=["/health", "/public"]
        )
        
        @app.get("/me")
        async def me(request: Request):
            user = request.state.globalauth_user
            return {"id": user.id}
        ```
    """
    
    DEFAULT_EXCLUDE_PATHS = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }
    
    def __init__(
        self,
        app,
        client: GlobalAuthClient,
        exclude_paths: list[str] | None = None,
        on_error: Callable[[Request, Exception], Response] | None = None,
    ):
        super().__init__(app)
        self.client = client
        self.on_error = on_error
        
        # Build exclude paths set
        self.exclude_paths = set(self.DEFAULT_EXCLUDE_PATHS)
        if exclude_paths:
            self.exclude_paths.update(exclude_paths)
    
    def _should_skip(self, path: str) -> bool:
        """Check if path should skip authentication"""
        # Exact match
        if path in self.exclude_paths:
            return True
        
        # Prefix match for paths like /docs/xxx
        for exclude_path in self.exclude_paths:
            if exclude_path.endswith("*") and path.startswith(exclude_path[:-1]):
                return True
        
        return False
    
    def _get_token(self, request: Request) -> str | None:
        """Extract Bearer token from Authorization header"""
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return None
        
        if not auth_header.startswith("Bearer "):
            return None
        
        return auth_header[7:]
    
    def _error_response(
        self,
        request: Request,
        error: Exception,
    ) -> Response:
        """Create error response"""
        # Custom error handler
        if self.on_error:
            return self.on_error(request, error)
        
        # Default error responses
        if isinstance(error, TokenExpiredError):
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Token expired",
                    "error_code": "TOKEN_EXPIRED",
                }
            )
        
        elif isinstance(error, UserBannedError):
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "User is banned",
                    "error_code": "USER_BANNED",
                }
            )
        
        elif isinstance(error, (TokenInvalidError, AuthenticationError)):
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid token",
                    "error_code": "INVALID_TOKEN",
                }
            )
        
        elif isinstance(error, ConnectionError):
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Auth service unavailable",
                    "error_code": "SERVICE_UNAVAILABLE",
                }
            )
        
        else:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Authentication required",
                    "error_code": "AUTH_REQUIRED",
                }
            )
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request"""
        # Skip excluded paths
        if self._should_skip(request.url.path):
            return await call_next(request)
        
        # Get token
        token = self._get_token(request)
        
        if not token:
            return self._error_response(request, AuthenticationError("No token provided"))
        
        # Validate token
        try:
            user = await self.client.introspect(token)
        except Exception as e:
            return self._error_response(request, e)
        
        # Store user in request state
        request.state.globalauth_user = user
        
        # Continue
        return await call_next(request)
