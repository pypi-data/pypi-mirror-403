"""Base channel class for protocol implementations.

This module provides the abstract base class for all channel implementations.
Channels are responsible for exposing LangGraph assistants through various
protocols and platforms.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from starlette.routing import BaseRoute

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response


class BaseChannel(ABC):
    """Abstract base class for channel implementations.

    A channel is responsible for:
    1. Defining API routes for a specific protocol
    2. Converting protocol-specific requests to LangGraph format
    3. Converting LangGraph responses to protocol-specific format

    Example:
        >>> class MyChannel(BaseChannel):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my-channel"
        ...
        ...     @property
        ...     def routes(self) -> list[BaseRoute]:
        ...         return [ApiRoute("/my-channel/endpoint", self.handle)]
        ...
        ...     async def handle(self, request: Request) -> Response:
        ...         # Handle the request
        ...         pass
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the channel name.

        Returns:
            A unique identifier for this channel (e.g., "wework", "openai", "slack")
        """
        ...

    @property
    @abstractmethod
    def routes(self) -> list[BaseRoute]:
        """Return the list of routes for this channel.

        Returns:
            List of Starlette Route objects
        """
        ...

    @property
    def config_key(self) -> str:
        """Return the configuration key to disable this channel.

        By default, returns "disable_{name}".

        Returns:
            Configuration key string (e.g., "disable_wework")
        """
        return f"disable_{self.name}"

    def is_enabled(self, config: dict | None) -> bool:
        """Check if this channel is enabled based on configuration.

        Args:
            config: HTTP configuration dictionary

        Returns:
            True if the channel is enabled, False otherwise
        """
        if config is None:
            return True
        return not config.get(self.config_key, False)
