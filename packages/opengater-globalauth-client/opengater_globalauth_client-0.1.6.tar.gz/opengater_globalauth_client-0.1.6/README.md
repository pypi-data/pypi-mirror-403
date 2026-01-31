# opengater-globalauth-client

Python client library for GlobalAuth authentication service.

## Features

- 🔐 HTTP client for token validation and referral operations
- 🐰 RabbitMQ integration for events and commands
- ⚡ FastAPI middleware and dependencies
- 💾 Built-in caching for introspect results
- 🔄 Async-first design

## Installation

```bash
pip install opengater-globalauth-client
```

Or with uv:

```bash
uv add opengater-globalauth-client
```

## Quick Start

### HTTP Client

```python
from opengater_globalauth_client import GlobalAuthClient

client = GlobalAuthClient(
    base_url="https://auth.example.com",
    service_slug="opengater",
    cache_ttl=300  # Cache introspect results for 5 minutes
)

# Validate token
user = await client.introspect(token)
print(f"User: {user.id}, verified: {user.verified}")

# Decode referral code
ref_info = await client.decode_referral("ref_xxx")
if ref_info.type == "referral":
    print(f"Invited by: {ref_info.inviter_id}")

# Get referral link for user
link = await client.get_referral_link(user_token)
print(f"Share this link: {link.link}")

# Get referral stats
stats = await client.get_referral_stats(user_token)
print(f"Total invited: {stats.total_invited}")
```

### RabbitMQ Integration

```python
from faststream.rabbit import RabbitBroker
from opengater_globalauth_client.broker import (
    GlobalAuthConsumer,
    GlobalAuthPublisher,
    UserCreatedEvent,
)

# Use your existing broker
broker = RabbitBroker(settings.rabbitmq_url)

# Consumer for events
consumer = GlobalAuthConsumer(broker, "globalauth.opengater")

@consumer.on_user_created
async def handle_user_created(event: UserCreatedEvent):
    print(f"New user: {event.user_id}")
    
    if event.invited_by_id:
        # Award referral bonus
        await award_bonus(event.invited_by_id)

@consumer.on_auth_method_linked
async def handle_linked(event):
    print(f"User {event.user_id} linked {event.auth_type}")

# Publisher for commands
publisher = GlobalAuthPublisher(broker)

# Create user from Telegram bot
await publisher.create_user(
    auth_type="telegram",
    identifier="123456789",
    extra_data={"username": "john", "first_name": "John"},
    invited_by_id="uuid-of-inviter"
)
```

### FastAPI Integration

#### With Middleware (Recommended)

```python
from fastapi import FastAPI, Depends, Request
from opengater_globalauth_client import GlobalAuthClient
from opengater_globalauth_client.fastapi import AuthMiddleware, get_current_user

app = FastAPI()

client = GlobalAuthClient(
    base_url="https://auth.example.com",
    service_slug="opengater"
)

# Add middleware for automatic token validation
app.add_middleware(
    AuthMiddleware,
    client=client,
    exclude_paths=["/health", "/public/*"]  # Optional
)

@app.get("/me")
async def me(user = Depends(get_current_user())):
    return {
        "id": user.id,
        "verified": user.verified,
        "trust_level": user.trust.level
    }

@app.get("/admin-only")
async def admin_only(user = Depends(require_admin())):
    return {"message": "Welcome, admin!"}
```

#### Without Middleware

```python
from fastapi import FastAPI, Depends
from opengater_globalauth_client import GlobalAuthClient
from opengater_globalauth_client.fastapi import get_current_user

app = FastAPI()

client = GlobalAuthClient(
    base_url="https://auth.example.com",
    service_slug="opengater"
)

# Pass client to dependency
@app.get("/me")
async def me(user = Depends(get_current_user(client))):
    return {"id": user.id}
```

## Available Events

| Event | Description |
|-------|-------------|
| `user_created` | New user registered |
| `auth_method_linked` | User linked auth method (email, telegram) |
| `auth_method_unlinked` | User unlinked auth method |
| `user_banned` | User was banned |
| `user_unbanned` | User was unbanned |

## User Model

```python
class User:
    id: str
    verified: bool
    is_banned: bool
    is_admin: bool
    trust: TrustInfo  # score, level
    auth_methods: list[AuthMethod]
    invited_by_id: str | None
    registered_via_event: str | None
    registered_via_service: str | None
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `base_url` | GlobalAuth service URL | Required |
| `service_slug` | Your service identifier | Required |
| `cache_ttl` | Introspect cache TTL (seconds) | 300 |
| `timeout` | HTTP timeout (seconds) | 30 |

## Error Handling

```python
from opengater_globalauth_client import (
    GlobalAuthClient,
    TokenExpiredError,
    TokenInvalidError,
    UserBannedError,
    ConnectionError,
)

try:
    user = await client.introspect(token)
except TokenExpiredError:
    # Token expired, need to refresh
    pass
except UserBannedError:
    # User is banned
    pass
except TokenInvalidError:
    # Invalid token
    pass
except ConnectionError:
    # GlobalAuth service unavailable
    pass
```

## License

MIT
