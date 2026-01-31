"""
Pydantic models for GlobalAuth client.
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class TrustInfo(BaseModel):
    """Trust score information"""
    score: int
    level: str
    methods_count: int = 0
    verified_methods_count: int = 0
    has_email: bool = False
    has_telegram: bool = False
    missing_methods: list[str] = []
    potential_score: int = 0


class AuthMethod(BaseModel):
    """Authentication method"""
    auth_type: str
    identifier: str
    verified: bool
    extra_data: dict | None = None


class User(BaseModel):
    """User information from introspect"""
    active: bool
    user_id: str | None = None
    verified: bool | None = None
    is_admin: bool = False
    is_banned: bool = False
    created_at: datetime | None = None
    last_login_at: datetime | None = None
    
    # Auth method data
    email: str | None = None
    telegram_id: int | None = None
    telegram_username: str | None = None
    telegram_first_name: str | None = None
    telegram_last_name: str | None = None
    
    # All auth methods
    auth_methods: list[AuthMethod] = []
    
    # Trust info
    trust: TrustInfo | None = None
    
    # Token info
    token_type: str | None = None
    exp: int | None = None
    
    @property
    def id(self) -> str | None:
        """Alias for user_id"""
        return self.user_id
    
    @property
    def is_active(self) -> bool:
        """Alias for active"""
        return self.active


class ReferralLink(BaseModel):
    """Referral link response"""
    link: str
    code: str
    type: Literal["referral"]
    service: str


class EventLink(BaseModel):
    """Event link response"""
    link: str
    code: str
    type: Literal["event"]
    event_id: str
    service: str


class DecodedReferral(BaseModel):
    """Decoded referral code"""
    type: Literal["referral"]
    inviter_id: str


class DecodedEvent(BaseModel):
    """Decoded event code"""
    type: Literal["event"]
    event_id: str
    service_slug: str


class ReferralStats(BaseModel):
    """Referral statistics"""
    total_invited: int
    invited_users: list[dict]


class InviterInfo(BaseModel):
    """Inviter information"""
    inviter_id: str
    invited_at: str


class TokenResponse(BaseModel):
    """Token response from auth endpoints"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class ServiceInfo(BaseModel):
    """Registered service information"""
    id: str
    name: str
    slug: str
    public_url: str | None
    webhook_url: str | None
    use_rabbitmq: bool
    rabbitmq_queue: str
    is_active: bool
