"""
GlobalAuth client library.

A Python client for GlobalAuth authentication service with RabbitMQ
and FastAPI integration.

Example:
    ```python
    from opengater_globalauth_client import GlobalAuthClient
    from opengater_globalauth_client.broker import GlobalAuthConsumer, GlobalAuthPublisher
    from opengater_globalauth_client.fastapi import AuthMiddleware, get_current_user
    
    # HTTP client
    client = GlobalAuthClient(
        base_url="https://auth.example.com",
        service_slug="opengater",
        cache_ttl=300  # seconds
    )
    
    # Validate token
    user = await client.introspect(token)
    print(f"User: {user.id}, verified: {user.verified}")
    
    # Referral operations
    ref_info = await client.decode_referral("ref_xxx")
    link = await client.get_referral_link(user_token)
    ```

RabbitMQ integration:
    ```python
    from faststream.rabbit import RabbitBroker
    from opengater_globalauth_client.broker import GlobalAuthConsumer, GlobalAuthPublisher
    
    broker = RabbitBroker(settings.rabbitmq_url)
    
    # Consumer for events
    consumer = GlobalAuthConsumer(broker, "globalauth.opengater")
    
    @consumer.on_user_created
    async def handle_user(event):
        print(f"New user: {event.user_id}")
    
    # Publisher for commands
    publisher = GlobalAuthPublisher(broker)
    await publisher.create_user(auth_type="telegram", identifier="123")
    ```

FastAPI integration:
    ```python
    from fastapi import FastAPI, Depends
    from opengater_globalauth_client import GlobalAuthClient
    from opengater_globalauth_client.fastapi import AuthMiddleware, get_current_user
    
    app = FastAPI()
    client = GlobalAuthClient(base_url="...", service_slug="opengater")
    
    # Automatic token validation
    app.add_middleware(AuthMiddleware, client=client)
    
    @app.get("/me")
    async def me(user = Depends(get_current_user())):
        return {"id": user.id}
    ```
"""

__version__ = "0.1.3"

from opengater_globalauth_client.client import GlobalAuthClient
from opengater_globalauth_client.models import (
    User,
    AuthMethod,
    TrustInfo,
    ReferralLink,
    EventLink,
    DecodedReferral,
    DecodedEvent,
    ReferralStats,
    InviterInfo,
    TokenResponse,
    ServiceInfo,
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
    ValidationError,
)

__all__ = [
    # Version
    "__version__",
    
    # Client
    "GlobalAuthClient",
    
    # Models
    "User",
    "AuthMethod",
    "TrustInfo",
    "ReferralLink",
    "EventLink",
    "DecodedReferral",
    "DecodedEvent",
    "ReferralStats",
    "InviterInfo",
    "TokenResponse",
    "ServiceInfo",
    
    # Exceptions
    "GlobalAuthError",
    "AuthenticationError",
    "TokenExpiredError",
    "TokenInvalidError",
    "UserBannedError",
    "ConnectionError",
    "ServiceUnavailableError",
    "NotFoundError",
    "ValidationError",
]
