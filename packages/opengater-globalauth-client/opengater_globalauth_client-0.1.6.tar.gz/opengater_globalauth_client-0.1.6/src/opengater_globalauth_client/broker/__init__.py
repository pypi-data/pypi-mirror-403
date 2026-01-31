"""
RabbitMQ broker integration for GlobalAuth.
"""
from opengater_globalauth_client.broker.consumer import GlobalAuthConsumer
from opengater_globalauth_client.broker.publisher import GlobalAuthPublisher
from opengater_globalauth_client.broker.events import (
    UserCreatedEvent,
    AuthMethodLinkedEvent,
    AuthMethodUnlinkedEvent,
    UserBannedEvent,
    UserUnbannedEvent,
    CreateUserCommand,
)

__all__ = [
    "GlobalAuthConsumer",
    "GlobalAuthPublisher",
    "UserCreatedEvent",
    "AuthMethodLinkedEvent",
    "AuthMethodUnlinkedEvent",
    "UserBannedEvent",
    "UserUnbannedEvent",
    "CreateUserCommand",
]
