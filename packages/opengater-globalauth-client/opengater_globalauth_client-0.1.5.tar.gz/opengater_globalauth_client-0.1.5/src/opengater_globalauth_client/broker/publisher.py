"""
RabbitMQ publisher for GlobalAuth commands.
"""
from pydantic import BaseModel

from faststream.rabbit import RabbitBroker

from opengater_globalauth_client.broker.events import CreateUserCommand


class GlobalAuthPublisher:
    """
    Publisher for sending commands to GlobalAuth via RabbitMQ.
    
    Uses existing RabbitBroker instance from your application.
    
    Args:
        broker: RabbitBroker instance
    
    Example:
        ```python
        from faststream.rabbit import RabbitBroker
        from opengater_globalauth_client.broker import GlobalAuthPublisher
        
        broker = RabbitBroker(settings.rabbitmq_url)
        publisher = GlobalAuthPublisher(broker)
        
        # Create user from Telegram bot
        await publisher.create_user(
            auth_type="telegram",
            identifier="123456789",
            extra_data={"username": "john", "first_name": "John"},
            invited_by_id="uuid-of-inviter"
        )
        ```
    """
    
    COMMANDS_QUEUE = "globalauth.commands"
    
    def __init__(self, broker: RabbitBroker):
        self.broker = broker
    
    async def _publish(self, message: BaseModel) -> None:
        """Publish message to commands queue"""
        await self.broker.publish(
            message.model_dump(mode="json"),
            queue=self.COMMANDS_QUEUE,
            persist=True,
        )
    
    async def create_user(
        self,
        auth_type: str,
        identifier: str,
        extra_data: dict | None = None,
        invited_by_id: str | None = None,
        event_id: str | None = None,
        event_service: str | None = None,
    ) -> None:
        """
        Send create_user command to GlobalAuth.
        
        GlobalAuth will create the user and publish user_created event.
        
        Args:
            auth_type: Authentication type ("telegram")
            identifier: User identifier (e.g., telegram_id)
            extra_data: Additional data (username, first_name, etc.)
            invited_by_id: UUID of inviter (referral)
            event_id: Event/campaign ID
            event_service: Service slug for event
        
        Note:
            invited_by_id and (event_id + event_service) are mutually exclusive.
            You can specify either a referrer OR an event, not both.
        
        Example:
            ```python
            # Referral registration
            await publisher.create_user(
                auth_type="telegram",
                identifier="123456789",
                invited_by_id="uuid-of-inviter"
            )
            
            # Event/campaign registration
            await publisher.create_user(
                auth_type="telegram", 
                identifier="123456789",
                event_id="black_friday_2025",
                event_service="opengater"
            )
            ```
        """
        command = CreateUserCommand(
            auth_type=auth_type,
            identifier=identifier,
            extra_data=extra_data,
            invited_by_id=invited_by_id,
            event_id=event_id,
            event_service=event_service,
        )
        
        await self._publish(command)
    
    async def send_command(self, command: str, **kwargs) -> None:
        """
        Send generic command to GlobalAuth.
        
        Use this for custom commands or future API extensions.
        
        Args:
            command: Command name
            **kwargs: Command parameters
        """
        message = {"command": command, **kwargs}
        
        await self.broker.publish(
            message,
            queue=self.COMMANDS_QUEUE,
            persist=True,
        )
