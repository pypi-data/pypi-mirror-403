"""
GlobalAuth HTTP client with caching.
"""
import asyncio
from datetime import datetime, timedelta
from typing import TypeVar
from dataclasses import dataclass, field

import httpx

from opengater_globalauth_client.models import (
    User,
    ReferralLink,
    DecodedReferral,
    DecodedEvent,
    ReferralStats,
    InviterInfo,
)
from opengater_globalauth_client.exceptions import (
    GlobalAuthError,
    AuthenticationError,
    TokenExpiredError,
    TokenInvalidError,
    UserBannedError,
    ConnectionError,
    ServiceUnavailableError,
    NotFoundError,
)


T = TypeVar("T")


@dataclass
class CacheEntry:
    """Cache entry with expiration"""
    value: T
    expires_at: datetime


@dataclass
class Cache:
    """Simple in-memory cache with TTL"""
    _data: dict[str, CacheEntry] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    async def get(self, key: str) -> T | None:
        """Get value from cache if not expired"""
        async with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            
            if datetime.utcnow() > entry.expires_at:
                del self._data[key]
                return None
            
            return entry.value
    
    async def set(self, key: str, value: T, ttl_seconds: int) -> None:
        """Set value in cache with TTL"""
        async with self._lock:
            self._data[key] = CacheEntry(
                value=value,
                expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds)
            )
    
    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        async with self._lock:
            self._data.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all cache"""
        async with self._lock:
            self._data.clear()
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries, return count of removed"""
        async with self._lock:
            now = datetime.utcnow()
            expired = [k for k, v in self._data.items() if now > v.expires_at]
            for key in expired:
                del self._data[key]
            return len(expired)


class GlobalAuthClient:
    """
    HTTP client for GlobalAuth service.
    
    Args:
        base_url: Base URL of GlobalAuth service (e.g., "https://auth.example.com")
        service_slug: Your service slug (e.g., "opengater")
        cache_ttl: Cache TTL in seconds for introspect results (default: 300)
        timeout: HTTP timeout in seconds (default: 30)
        trust_env: Trust environment variables for proxy settings (default: False)
    
    Example:
        ```python
        client = GlobalAuthClient(
            base_url="https://auth.example.com",
            service_slug="opengater",
            cache_ttl=300
        )
        
        user = await client.introspect(token)
        ref_info = await client.decode_referral("ref_xxx")
        ```
    """
    
    def __init__(
        self,
        base_url: str,
        service_slug: str,
        cache_ttl: int = 300,
        timeout: int = 30,
        trust_env: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.service_slug = service_slug
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self.trust_env = trust_env
        
        self._cache = Cache()
        self._http_client: httpx.AsyncClient | None = None
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                trust_env=self.trust_env,
            )
        return self._http_client
    
    async def close(self) -> None:
        """Close HTTP client and clear cache"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        await self._cache.clear()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # ================================================================
    # Error handling
    # ================================================================
    
    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses"""
        if response.status_code == 200:
            return
        
        try:
            data = response.json()
            detail = data.get("detail", "Unknown error")
        except Exception:
            detail = response.text or "Unknown error"
        
        if response.status_code == 401:
            if "expired" in detail.lower():
                raise TokenExpiredError(detail)
            elif "banned" in detail.lower():
                raise UserBannedError(detail)
            else:
                raise TokenInvalidError(detail)
        
        elif response.status_code == 403:
            raise AuthenticationError(detail)
        
        elif response.status_code == 404:
            raise NotFoundError(detail)
        
        elif response.status_code >= 500:
            raise ServiceUnavailableError(detail)
        
        else:
            raise GlobalAuthError(f"HTTP {response.status_code}: {detail}")
    
    # ================================================================
    # Token operations
    # ================================================================
    
    async def introspect(
        self,
        token: str,
        skip_cache: bool = False,
    ) -> User:
        """
        Introspect access token and get user information.
        
        Results are cached for `cache_ttl` seconds.
        
        Args:
            token: JWT access token
            skip_cache: Skip cache and always fetch from server
        
        Returns:
            User object with full information
        
        Raises:
            TokenExpiredError: Token has expired
            TokenInvalidError: Token is invalid
            UserBannedError: User is banned
        """
        cache_key = f"introspect:{token[:32]}"
        
        # Check cache
        if not skip_cache:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return cached
        
        # Fetch from server
        try:
            response = await self.http_client.post(
                "/auth/jwt/introspect",
                json={"token": token},
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to GlobalAuth: {e}")
        
        self._handle_error(response)
        
        data = response.json()
        user = User(**data)
        
        # Check if token is active
        if not user.active:
            raise TokenInvalidError("Token is not active")
        
        # Cache result
        await self._cache.set(cache_key, user, self.cache_ttl)
        
        return user
    
    async def invalidate_token_cache(self, token: str) -> None:
        """Remove token from cache (e.g., after logout)"""
        cache_key = f"introspect:{token[:32]}"
        await self._cache.delete(cache_key)
    
    async def refresh_token(
        self,
        refresh_token: str,
    ) -> dict:
        """
        Refresh access token.
        
        Args:
            refresh_token: JWT refresh token
        
        Returns:
            Dict with access_token, refresh_token, expires_in
        """
        try:
            response = await self.http_client.post(
                "/auth/jwt/refresh",
                json={"refresh_token": refresh_token},
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to GlobalAuth: {e}")
        
        self._handle_error(response)
        
        return response.json()
    
    # ================================================================
    # Referral operations
    # ================================================================
    
    async def get_referral_link(self, user_token: str) -> ReferralLink:
        """
        Get referral link for current user.
        
        Args:
            user_token: User's JWT access token
        
        Returns:
            ReferralLink with link and code
        """
        try:
            response = await self.http_client.get(
                "/referrals/link",
                headers={"Authorization": f"Bearer {user_token}"},
                params={"service": self.service_slug},
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to GlobalAuth: {e}")
        
        self._handle_error(response)
        
        return ReferralLink(**response.json())
    
    async def decode_referral(
        self,
        code: str,
    ) -> DecodedReferral | DecodedEvent:
        """
        Decode referral or event code.
        
        Args:
            code: Referral code (ref_xxx or evt_xxx)
        
        Returns:
            DecodedReferral or DecodedEvent depending on code type
        """
        try:
            response = await self.http_client.get(
                "/referrals/decode",
                params={"code": code},
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to GlobalAuth: {e}")
        
        self._handle_error(response)
        
        data = response.json()
        
        if data["type"] == "referral":
            return DecodedReferral(**data)
        else:
            return DecodedEvent(**data)
    
    async def get_referral_stats(self, user_token: str) -> ReferralStats:
        """
        Get referral statistics for current user.
        
        Args:
            user_token: User's JWT access token
        
        Returns:
            ReferralStats with total_invited and invited_users list
        """
        try:
            response = await self.http_client.get(
                "/referrals/my/stats",
                headers={"Authorization": f"Bearer {user_token}"},
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to GlobalAuth: {e}")
        
        self._handle_error(response)
        
        return ReferralStats(**response.json())
    
    async def get_inviter(self, user_token: str) -> InviterInfo | None:
        """
        Get information about who invited current user.
        
        Args:
            user_token: User's JWT access token
        
        Returns:
            InviterInfo or None if user wasn't invited
        """
        try:
            response = await self.http_client.get(
                "/referrals/my/invited-by",
                headers={"Authorization": f"Bearer {user_token}"},
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to GlobalAuth: {e}")
        
        self._handle_error(response)
        
        data = response.json()
        
        if data is None:
            return None
        
        return InviterInfo(**data)
    
    # ================================================================
    # Health check
    # ================================================================
    
    async def health_check(self) -> bool:
        """
        Check if GlobalAuth service is healthy.
        
        Returns:
            True if service is healthy
        """
        try:
            response = await self.http_client.get("/health")
            return response.status_code == 200
        except Exception:
            return False
    
    # ================================================================
    # Cache management
    # ================================================================
    
    async def clear_cache(self) -> None:
        """Clear all cached data"""
        await self._cache.clear()
    
    async def cleanup_cache(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of removed entries
        """
        return await self._cache.cleanup_expired()
