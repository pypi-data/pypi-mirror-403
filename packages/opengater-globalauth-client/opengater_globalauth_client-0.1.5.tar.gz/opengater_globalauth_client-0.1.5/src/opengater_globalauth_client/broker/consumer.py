"""
RabbitMQ consumer for GlobalAuth events.
"""
from typing import Callable, Awaitable
from functools import wraps

from faststream import AckPolicy
from faststream.rabbit import RabbitBroker, RabbitQueue, RabbitExchange, ExchangeType

from opengater_globalauth_client.broker.events import (
    UserCreatedEvent,
    AuthMethodLinkedEvent,
    AuthMethodUnlinkedEvent,
    UserBannedEvent,
    UserUnbannedEvent,
)


class GlobalAuthConsumer:
    """
    Consumer for GlobalAuth events from RabbitMQ.
    
    Uses existing RabbitBroker instance from your application.
    
    Args:
        broker: RabbitBroker instance
        queue_name: Queue name to consume from (e.g., "globalauth.opengater")
    
    Example:
        ```python
        from faststream.rabbit import RabbitBroker
        from opengater_globalauth_client.broker import GlobalAuthConsumer
        
        broker = RabbitBroker(settings.rabbitmq_url)
        consumer = GlobalAuthConsumer(broker, "globalauth.opengater")
        
        @consumer.on_user_created
        async def handle_user_created(event: UserCreatedEvent):
            print(f"New user: {event.user_id}")
            if event.invited_by_id:
                # Award referral bonus
                pass
        
        @consumer.on_auth_method_linked
        async def handle_linked(event: AuthMethodLinkedEvent):
            print(f"User {event.user_id} linked {event.auth_type}")
        ```
    """
    
    def __init__(
        self,
        broker: RabbitBroker,
        queue_name: str,
    ):
        self.broker = broker
        self.queue_name = queue_name
        
        # Exchange для событий GlobalAuth
        self._exchange = RabbitExchange(
            "globalauth.events",
            type=ExchangeType.FANOUT,
            durable=True,
        )
        
        # Очередь для получения событий
        self._queue = RabbitQueue(
            queue_name,
            durable=True,
        )
        
        # Registered handlers
        self._handlers: dict[str, Callable] = {}
    
    def _create_handler(
        self,
        event_type: str,
        event_class: type,
    ) -> Callable:
        """Create decorator for event handler"""
        
        def decorator(func: Callable[[event_class], Awaitable[None]]):
            # Store handler
            self._handlers[event_type] = func
            
            # Register with broker
            @self.broker.subscriber(
                self._queue,
                self._exchange,
                ack_policy=AckPolicy.REJECT_ON_ERROR,
                filter=lambda msg: msg.get("event") == event_type,
            )
            @wraps(func)
            async def wrapper(data: dict):
                event = event_class(**data)
                await func(event)
            
            return func
        
        return decorator
    
    @property
    def on_user_created(self) -> Callable:
        """
        Decorator for user_created event handler.
        
        Example:
            ```python
            @consumer.on_user_created
            async def handle(event: UserCreatedEvent):
                print(f"New user: {event.user_id}")
            ```
        """
        return self._create_handler("user_created", UserCreatedEvent)
    
    @property
    def on_auth_method_linked(self) -> Callable:
        """
        Decorator for auth_method_linked event handler.
        
        Example:
            ```python
            @consumer.on_auth_method_linked
            async def handle(event: AuthMethodLinkedEvent):
                print(f"User {event.user_id} linked {event.auth_type}")
            ```
        """
        return self._create_handler("auth_method_linked", AuthMethodLinkedEvent)
    
    @property
    def on_auth_method_unlinked(self) -> Callable:
        """
        Decorator for auth_method_unlinked event handler.
        
        Example:
            ```python
            @consumer.on_auth_method_unlinked
            async def handle(event: AuthMethodUnlinkedEvent):
                print(f"User {event.user_id} unlinked {event.auth_type}")
            ```
        """
        return self._create_handler("auth_method_unlinked", AuthMethodUnlinkedEvent)
    
    @property
    def on_user_banned(self) -> Callable:
        """
        Decorator for user_banned event handler.
        
        Example:
            ```python
            @consumer.on_user_banned
            async def handle(event: UserBannedEvent):
                print(f"User {event.user_id} was banned")
            ```
        """
        return self._create_handler("user_banned", UserBannedEvent)
    
    @property
    def on_user_unbanned(self) -> Callable:
        """
        Decorator for user_unbanned event handler.
        
        Example:
            ```python
            @consumer.on_user_unbanned
            async def handle(event: UserUnbannedEvent):
                print(f"User {event.user_id} was unbanned")
            ```
        """
        return self._create_handler("user_unbanned", UserUnbannedEvent)
    
    def on_event(self, event_type: str) -> Callable:
        """
        Generic decorator for any event type.
        
        Use this if you need to handle custom events or
        handle raw event data.
        
        Example:
            ```python
            @consumer.on_event("custom_event")
            async def handle(data: dict):
                print(f"Custom event: {data}")
            ```
        """
        def decorator(func: Callable[[dict], Awaitable[None]]):
            self._handlers[event_type] = func
            
            @self.broker.subscriber(
                self._queue,
                self._exchange,
                ack_policy=AckPolicy.REJECT_ON_ERROR,
                filter=lambda msg: msg.get("event") == event_type,
            )
            @wraps(func)
            async def wrapper(data: dict):
                await func(data)
            
            return func
        
        return decorator
