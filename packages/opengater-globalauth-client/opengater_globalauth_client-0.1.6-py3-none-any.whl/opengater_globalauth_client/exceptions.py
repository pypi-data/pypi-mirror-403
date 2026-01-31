"""
Exceptions for GlobalAuth client.
"""


class GlobalAuthError(Exception):
    """Base exception for GlobalAuth client"""
    pass


class AuthenticationError(GlobalAuthError):
    """Authentication failed"""
    pass


class TokenExpiredError(AuthenticationError):
    """Token has expired"""
    pass


class TokenInvalidError(AuthenticationError):
    """Token is invalid"""
    pass


class UserBannedError(AuthenticationError):
    """User is banned"""
    pass


class ConnectionError(GlobalAuthError):
    """Failed to connect to GlobalAuth service"""
    pass


class ServiceUnavailableError(GlobalAuthError):
    """GlobalAuth service is unavailable"""
    pass


class NotFoundError(GlobalAuthError):
    """Resource not found"""
    pass


class ValidationError(GlobalAuthError):
    """Validation error"""
    pass
