"""
Event and command models for RabbitMQ.
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


# ================================================================
# Base
# ================================================================

class BrokerMessage(BaseModel):
    """Base broker message"""
    
    class Config:
        extra = "allow"


# ================================================================
# Events (IN) - from GlobalAuth
# ================================================================

class TrustInfo(BaseModel):
    """Trust score information"""
    score: int
    level: str


class UserCreatedEvent(BrokerMessage):
    """Event: new user created"""
    event: Literal["user_created"] = "user_created"
    timestamp: datetime
    
    user_id: str
    auth_type: str
    identifier: str
    extra_data: dict | None = None
    trust: TrustInfo
    
    # Registration source (optional)
    invited_by_id: str | None = None
    registered_via_event: str | None = None
    registered_via_service: str | None = None


class AuthMethodLinkedEvent(BrokerMessage):
    """Event: auth method linked"""
    event: Literal["auth_method_linked"] = "auth_method_linked"
    timestamp: datetime
    
    user_id: str
    auth_type: str
    identifier: str
    verified: bool
    is_first_link: bool
    times_linked: int
    trust: TrustInfo
    extra_data: dict | None = None


class AuthMethodUnlinkedEvent(BrokerMessage):
    """Event: auth method unlinked"""
    event: Literal["auth_method_unlinked"] = "auth_method_unlinked"
    timestamp: datetime
    
    user_id: str
    auth_type: str
    identifier: str
    unlinked_by: Literal["user", "admin"]
    trust: TrustInfo


class UserBannedEvent(BrokerMessage):
    """Event: user banned"""
    event: Literal["user_banned"] = "user_banned"
    timestamp: datetime
    
    user_id: str
    banned_by: str


class UserUnbannedEvent(BrokerMessage):
    """Event: user unbanned"""
    event: Literal["user_unbanned"] = "user_unbanned"
    timestamp: datetime
    
    user_id: str
    unbanned_by: str


# ================================================================
# Commands (OUT) - to GlobalAuth
# ================================================================

class CreateUserCommand(BrokerMessage):
    """Command: create user"""
    command: Literal["create_user"] = "create_user"
    
    auth_type: Literal["telegram"]
    identifier: str
    extra_data: dict | None = None
    
    # Registration source (optional, mutually exclusive)
    invited_by_id: str | None = None
    event_id: str | None = None
    event_service: str | None = None
