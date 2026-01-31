"""A2A (Agent-to-Agent) channel with enhanced features.

This module provides A2A protocol endpoints with additional features from SDK:

1. Multi-Assistant support (existing):
   - /a2a/{assistant_id} - A2A endpoint for specific assistant
   - /.well-known/agent-card.json - Agent Card discovery

2. Enhanced features (from SDK):
   - InMemoryTaskStore - Persistent task state storage
   - PushNotificationConfigStore - Push notification configuration
   - A2AChannelConfig - Environment variable configuration

A2A Protocol specification:
https://a2a-protocol.org/dev/specification/

Endpoints:
    - POST /a2a/{assistant_id}              JSON-RPC (message/send, message/stream, tasks/*)
    - GET  /a2a/{assistant_id}              SSE stream (currently returns 405)
    - DELETE /a2a/{assistant_id}            Session termination (currently returns 405)
    - GET  /.well-known/agent-card.json     Agent Card discovery
"""

import asyncio
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

import httpx
import orjson
import structlog
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute

from orcakit_api.api.a2a import (
    ERROR_CODE_INVALID_PARAMS,
    ERROR_CODE_METHOD_NOT_FOUND,
    ERROR_CODE_PUSH_NOTIFICATION_NOT_SUPPORTED,
    ERROR_CODE_TASK_NOT_FOUND,
    A2A_PROTOCOL_VERSION,
    a2a_routes as existing_a2a_routes,
    generate_agent_card,
)
from orcakit_api.channels.base import BaseChannel
from orcakit_api.route import ApiRequest, ApiRoute

logger = structlog.stdlib.get_logger(__name__)


# ============================================================================
# Task Store Implementation (from SDK)
# ============================================================================


@dataclass
class StoredTask:
    """Stored task with metadata."""

    task_id: str
    context_id: str
    assistant_id: str
    status: str  # submitted, working, completed, failed, canceled, input-required
    created_at: float
    updated_at: float
    result: dict[str, Any] | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class InMemoryTaskStore:
    """In-memory task store for A2A tasks.

    Provides persistent task state storage without depending on LangGraph Server
    for task queries.

    Features:
    - LRU eviction when max_size is reached
    - TTL-based expiration
    - Thread-safe operations using asyncio.Lock
    """

    def __init__(self, max_size: int = 10000, ttl: float = 3600.0) -> None:
        """Initialize the task store.

        Args:
            max_size: Maximum number of tasks to store
            ttl: Time-to-live for tasks in seconds (default: 1 hour)
        """
        self._tasks: OrderedDict[str, StoredTask] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._lock = asyncio.Lock()

    async def create_task(
        self,
        task_id: str,
        context_id: str,
        assistant_id: str,
        status: str = "submitted",
        metadata: dict[str, Any] | None = None,
    ) -> StoredTask:
        """Create a new task.

        Args:
            task_id: Unique task identifier (run_id)
            context_id: Context identifier (thread_id)
            assistant_id: Assistant identifier
            status: Initial task status
            metadata: Optional metadata

        Returns:
            Created StoredTask
        """
        async with self._lock:
            now = time.time()
            task = StoredTask(
                task_id=task_id,
                context_id=context_id,
                assistant_id=assistant_id,
                status=status,
                created_at=now,
                updated_at=now,
                metadata=metadata or {},
            )
            self._tasks[task_id] = task
            self._evict_if_needed()
            return task

    async def get_task(self, task_id: str) -> StoredTask | None:
        """Get a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            StoredTask if found and not expired, None otherwise
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None

            # Check TTL
            if time.time() - task.created_at > self._ttl:
                del self._tasks[task_id]
                return None

            # Move to end (LRU)
            self._tasks.move_to_end(task_id)
            return task

    async def update_task(
        self,
        task_id: str,
        status: str | None = None,
        result: dict[str, Any] | None = None,
        history: list[dict[str, Any]] | None = None,
        artifacts: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredTask | None:
        """Update an existing task.

        Args:
            task_id: Task identifier
            status: New status (optional)
            result: Task result (optional)
            history: Message history (optional)
            artifacts: Task artifacts (optional)
            metadata: Additional metadata to merge (optional)

        Returns:
            Updated StoredTask if found, None otherwise
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None

            task.updated_at = time.time()
            if status is not None:
                task.status = status
            if result is not None:
                task.result = result
            if history is not None:
                task.history = history
            if artifacts is not None:
                task.artifacts = artifacts
            if metadata is not None:
                task.metadata.update(metadata)

            self._tasks.move_to_end(task_id)
            return task

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    async def list_tasks(
        self,
        context_id: str | None = None,
        assistant_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[StoredTask]:
        """List tasks with optional filters.

        Args:
            context_id: Filter by context ID
            assistant_id: Filter by assistant ID
            status: Filter by status
            limit: Maximum number of tasks to return

        Returns:
            List of matching StoredTask objects
        """
        async with self._lock:
            now = time.time()
            results = []

            for task in reversed(self._tasks.values()):
                # Skip expired tasks
                if now - task.created_at > self._ttl:
                    continue

                # Apply filters
                if context_id and task.context_id != context_id:
                    continue
                if assistant_id and task.assistant_id != assistant_id:
                    continue
                if status and task.status != status:
                    continue

                results.append(task)
                if len(results) >= limit:
                    break

            return results

    def _evict_if_needed(self) -> None:
        """Evict oldest tasks if max_size is exceeded."""
        while len(self._tasks) > self._max_size:
            self._tasks.popitem(last=False)


# ============================================================================
# Push Notification Store Implementation (from SDK)
# ============================================================================


@dataclass
class PushNotificationConfig:
    """Push notification configuration for a task."""

    task_id: str
    url: str
    token: str | None = None
    created_at: float = field(default_factory=time.time)


class InMemoryPushNotificationConfigStore:
    """In-memory store for push notification configurations.

    Stores webhook URLs for task completion notifications.
    """

    def __init__(self, max_size: int = 10000, ttl: float = 86400.0) -> None:
        """Initialize the push notification config store.

        Args:
            max_size: Maximum number of configs to store
            ttl: Time-to-live in seconds (default: 24 hours)
        """
        self._configs: OrderedDict[str, PushNotificationConfig] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._lock = asyncio.Lock()

    async def set_config(
        self,
        task_id: str,
        url: str,
        token: str | None = None,
    ) -> PushNotificationConfig:
        """Set push notification configuration for a task.

        Args:
            task_id: Task identifier
            url: Webhook URL to receive notifications
            token: Optional authentication token

        Returns:
            Created PushNotificationConfig
        """
        async with self._lock:
            config = PushNotificationConfig(
                task_id=task_id,
                url=url,
                token=token,
            )
            self._configs[task_id] = config
            self._evict_if_needed()
            return config

    async def get_config(self, task_id: str) -> PushNotificationConfig | None:
        """Get push notification config for a task.

        Args:
            task_id: Task identifier

        Returns:
            PushNotificationConfig if found and not expired, None otherwise
        """
        async with self._lock:
            config = self._configs.get(task_id)
            if config is None:
                return None

            # Check TTL
            if time.time() - config.created_at > self._ttl:
                del self._configs[task_id]
                return None

            return config

    async def delete_config(self, task_id: str) -> bool:
        """Delete push notification config.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if task_id in self._configs:
                del self._configs[task_id]
                return True
            return False

    def _evict_if_needed(self) -> None:
        """Evict oldest configs if max_size is exceeded."""
        while len(self._configs) > self._max_size:
            self._configs.popitem(last=False)


class PushNotificationSender:
    """Sends push notifications to configured webhooks."""

    def __init__(
        self,
        config_store: InMemoryPushNotificationConfigStore,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the push notification sender.

        Args:
            config_store: Push notification config store
            http_client: Optional HTTP client (creates one if not provided)
        """
        self._config_store = config_store
        self._http_client = http_client or httpx.AsyncClient(timeout=30.0)

    async def send_notification(
        self,
        task_id: str,
        event_type: str,
        data: dict[str, Any],
    ) -> bool:
        """Send a push notification for a task.

        Args:
            task_id: Task identifier
            event_type: Event type (e.g., "task.completed", "task.failed")
            data: Event data

        Returns:
            True if notification was sent successfully, False otherwise
        """
        config = await self._config_store.get_config(task_id)
        if config is None:
            return False

        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/pushNotification",
            "params": {
                "taskId": task_id,
                "event": event_type,
                "data": data,
            },
        }

        headers = {"Content-Type": "application/json"}
        if config.token:
            headers["Authorization"] = f"Bearer {config.token}"

        try:
            response = await self._http_client.post(
                config.url,
                content=orjson.dumps(payload),
                headers=headers,
            )
            return response.status_code < 400
        except Exception as e:
            await logger.awarning(
                "Failed to send push notification",
                task_id=task_id,
                url=config.url,
                error=str(e),
            )
            return False


# ============================================================================
# Channel Configuration (from SDK)
# ============================================================================


class A2AChannelConfig(BaseSettings):
    """Configuration for A2A channel with environment variable support.

    Environment variables are prefixed with A2A_ (e.g., A2A_NAME, A2A_STREAMING).

    Example:
        export A2A_NAME="My Agent"
        export A2A_DESCRIPTION="An intelligent assistant"
        export A2A_STREAMING=true
    """

    model_config = SettingsConfigDict(
        env_prefix="A2A_",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Agent Card settings
    name: str = Field(default="Agent", description="Default agent name")
    description: str = Field(
        default="AI Assistant", description="Default agent description"
    )
    version: str = Field(default="1.0.0", description="Agent version")

    # Capabilities
    streaming: bool = Field(default=True, description="Enable streaming support")
    push_notifications: bool = Field(
        default=True, description="Enable push notifications"
    )
    state_transition_history: bool = Field(
        default=False, description="Enable state transition history"
    )

    # Store settings
    task_store_max_size: int = Field(
        default=10000, description="Max tasks in memory store"
    )
    task_store_ttl: float = Field(
        default=3600.0, description="Task TTL in seconds"
    )
    push_config_max_size: int = Field(
        default=10000, description="Max push configs in memory store"
    )
    push_config_ttl: float = Field(
        default=86400.0, description="Push config TTL in seconds"
    )


# ============================================================================
# Global Stores (singleton instances)
# ============================================================================

_task_store: InMemoryTaskStore | None = None
_push_config_store: InMemoryPushNotificationConfigStore | None = None
_push_sender: PushNotificationSender | None = None
_config: A2AChannelConfig | None = None


def _get_config() -> A2AChannelConfig:
    """Get or create channel configuration."""
    global _config
    if _config is None:
        _config = A2AChannelConfig()
    return _config


def _get_task_store() -> InMemoryTaskStore:
    """Get or create task store."""
    global _task_store
    if _task_store is None:
        config = _get_config()
        _task_store = InMemoryTaskStore(
            max_size=config.task_store_max_size,
            ttl=config.task_store_ttl,
        )
    return _task_store


def _get_push_config_store() -> InMemoryPushNotificationConfigStore:
    """Get or create push notification config store."""
    global _push_config_store
    if _push_config_store is None:
        config = _get_config()
        _push_config_store = InMemoryPushNotificationConfigStore(
            max_size=config.push_config_max_size,
            ttl=config.push_config_ttl,
        )
    return _push_config_store


def _get_push_sender() -> PushNotificationSender:
    """Get or create push notification sender."""
    global _push_sender
    if _push_sender is None:
        _push_sender = PushNotificationSender(_get_push_config_store())
    return _push_sender


# ============================================================================
# Push Notification Endpoint Handlers
# ============================================================================


async def handle_push_notification_config_set(
    request: ApiRequest, params: dict[str, Any]
) -> dict[str, Any]:
    """Handle tasks/pushNotificationConfig/set request.

    Sets the push notification configuration for a task.

    Args:
        request: HTTP request
        params: Request params containing taskId and pushNotificationConfig

    Returns:
        {"result": {...}} or {"error": {...}}
    """
    task_id = params.get("id") or params.get("taskId")
    config_data = params.get("pushNotificationConfig", {})

    if not task_id:
        return {
            "error": {
                "code": ERROR_CODE_INVALID_PARAMS,
                "message": "Missing required parameter: id or taskId",
            }
        }

    url = config_data.get("url")
    if not url:
        return {
            "error": {
                "code": ERROR_CODE_INVALID_PARAMS,
                "message": "Missing required field: pushNotificationConfig.url",
            }
        }

    token = config_data.get("token")

    store = _get_push_config_store()
    await store.set_config(task_id, url, token)

    return {
        "result": {
            "taskId": task_id,
            "pushNotificationConfig": {
                "url": url,
                "token": token,
            },
        }
    }


async def handle_push_notification_config_get(
    request: ApiRequest, params: dict[str, Any]
) -> dict[str, Any]:
    """Handle tasks/pushNotificationConfig/get request.

    Gets the push notification configuration for a task.

    Args:
        request: HTTP request
        params: Request params containing taskId

    Returns:
        {"result": {...}} or {"error": {...}}
    """
    task_id = params.get("id") or params.get("taskId")

    if not task_id:
        return {
            "error": {
                "code": ERROR_CODE_INVALID_PARAMS,
                "message": "Missing required parameter: id or taskId",
            }
        }

    store = _get_push_config_store()
    config = await store.get_config(task_id)

    if config is None:
        return {
            "error": {
                "code": ERROR_CODE_TASK_NOT_FOUND,
                "message": f"Push notification config not found for task '{task_id}'",
            }
        }

    return {
        "result": {
            "taskId": task_id,
            "pushNotificationConfig": {
                "url": config.url,
                "token": config.token,
            },
        }
    }


async def handle_push_notification_config_delete(
    request: ApiRequest, params: dict[str, Any]
) -> dict[str, Any]:
    """Handle tasks/pushNotificationConfig/delete request.

    Deletes the push notification configuration for a task.

    Args:
        request: HTTP request
        params: Request params containing taskId

    Returns:
        {"result": {...}} or {"error": {...}}
    """
    task_id = params.get("id") or params.get("taskId")

    if not task_id:
        return {
            "error": {
                "code": ERROR_CODE_INVALID_PARAMS,
                "message": "Missing required parameter: id or taskId",
            }
        }

    store = _get_push_config_store()
    deleted = await store.delete_config(task_id)

    if not deleted:
        return {
            "error": {
                "code": ERROR_CODE_TASK_NOT_FOUND,
                "message": f"Push notification config not found for task '{task_id}'",
            }
        }

    return {
        "result": {
            "taskId": task_id,
            "deleted": True,
        }
    }


# ============================================================================
# Enhanced A2A Endpoint Handler
# ============================================================================


async def handle_enhanced_a2a_endpoint(request: ApiRequest) -> Response:
    """Enhanced A2A endpoint handler with push notification support.

    This handler intercepts push notification methods and delegates
    other methods to the existing A2A implementation.

    Args:
        request: The incoming HTTP request

    Returns:
        JSON-RPC response
    """
    from orcakit_api.api.a2a import handle_a2a_assistant_endpoint

    # Only intercept POST requests with push notification methods
    if request.method != "POST":
        return await handle_a2a_assistant_endpoint(request)

    try:
        body = await request.body()
        message = orjson.loads(body)
    except orjson.JSONDecodeError:
        return await handle_a2a_assistant_endpoint(request)

    if not isinstance(message, dict):
        return await handle_a2a_assistant_endpoint(request)

    method = message.get("method")
    params = message.get("params", {})
    request_id = message.get("id")

    # Handle push notification methods
    push_methods = {
        "tasks/pushNotificationConfig/set": handle_push_notification_config_set,
        "tasks/pushNotificationConfig/get": handle_push_notification_config_get,
        "tasks/pushNotificationConfig/delete": handle_push_notification_config_delete,
    }

    if method in push_methods:
        config = _get_config()
        if not config.push_notifications:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": ERROR_CODE_PUSH_NOTIFICATION_NOT_SUPPORTED,
                    "message": "Push notifications are not enabled",
                },
            })

        handler = push_methods[method]
        result_or_error = await handler(request, params)

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            **result_or_error,
        })

    # Delegate to existing A2A handler
    return await handle_a2a_assistant_endpoint(request)


async def handle_enhanced_agent_card_endpoint(request: ApiRequest) -> Response:
    """Enhanced Agent Card endpoint with configuration support.

    Uses A2AChannelConfig defaults when assistant-specific info is not available.

    Args:
        request: HTTP request

    Returns:
        JSON response with Agent Card
    """
    assistant_id = request.query_params.get("assistant_id")

    if not assistant_id:
        # Return error - assistant_id is required
        return JSONResponse(
            {
                "error": {
                    "code": ERROR_CODE_INVALID_PARAMS,
                    "message": "Missing required query parameter: assistant_id",
                }
            },
            status_code=400,
        )

    try:
        # Generate agent card using existing function
        agent_card = await generate_agent_card(request, assistant_id)

        # Enhance with config settings
        config = _get_config()
        agent_card["capabilities"]["pushNotifications"] = config.push_notifications
        agent_card["capabilities"]["stateTransitionHistory"] = (
            config.state_transition_history
        )

        return JSONResponse(agent_card)

    except ValueError as e:
        return JSONResponse(
            {
                "error": {
                    "code": ERROR_CODE_INVALID_PARAMS,
                    "message": str(e),
                }
            },
            status_code=400,
        )
    except Exception as e:
        await logger.aexception("Failed to generate agent card")
        return JSONResponse(
            {
                "error": {
                    "code": -32603,
                    "message": f"Internal server error: {str(e)}",
                }
            },
            status_code=500,
        )


# ============================================================================
# Route Definitions
# ============================================================================

# Enhanced routes with push notification support
enhanced_a2a_routes = [
    # Per-assistant A2A endpoints with push notification support
    ApiRoute(
        "/a2a/{assistant_id}",
        handle_enhanced_a2a_endpoint,
        methods=["GET", "POST", "DELETE"],
    ),
    # Enhanced Agent Card endpoint
    ApiRoute(
        "/.well-known/agent-card.json",
        handle_enhanced_agent_card_endpoint,
        methods=["GET"],
    ),
]


# ============================================================================
# Channel Class
# ============================================================================


class A2AChannel(BaseChannel):
    """A2A (Agent-to-Agent) channel with enhanced features.

    This channel provides A2A protocol endpoints with additional features:

    1. Multi-Assistant support:
       - /a2a/{assistant_id} - A2A endpoint for specific assistant
       - /.well-known/agent-card.json - Agent Card discovery

    2. Enhanced features (from SDK):
       - InMemoryTaskStore - Persistent task state storage
       - PushNotificationConfigStore - Push notification configuration
       - A2AChannelConfig - Environment variable configuration

    3. Push notification methods:
       - tasks/pushNotificationConfig/set
       - tasks/pushNotificationConfig/get
       - tasks/pushNotificationConfig/delete

    Example:
        >>> from orcakit_api.channels import A2AChannel
        >>> channel = A2AChannel()
        >>> print(channel.name)  # "a2a"
        >>> print(channel.routes)  # List of routes

    Environment variables:
        A2A_NAME: Default agent name
        A2A_DESCRIPTION: Default agent description
        A2A_STREAMING: Enable streaming (default: true)
        A2A_PUSH_NOTIFICATIONS: Enable push notifications (default: true)
        A2A_TASK_STORE_MAX_SIZE: Max tasks in store (default: 10000)
        A2A_TASK_STORE_TTL: Task TTL in seconds (default: 3600)
    """

    def __init__(self, config: A2AChannelConfig | None = None) -> None:
        """Initialize the A2A channel.

        Args:
            config: Optional configuration. If not provided, loads from environment.
        """
        global _config
        if config is not None:
            _config = config

    @property
    def name(self) -> str:
        """Return the channel name."""
        return "a2a"

    @property
    def routes(self) -> list[BaseRoute]:
        """Return the list of routes for this channel."""
        return enhanced_a2a_routes

    @property
    def task_store(self) -> InMemoryTaskStore:
        """Get the task store instance."""
        return _get_task_store()

    @property
    def push_config_store(self) -> InMemoryPushNotificationConfigStore:
        """Get the push notification config store instance."""
        return _get_push_config_store()

    @property
    def push_sender(self) -> PushNotificationSender:
        """Get the push notification sender instance."""
        return _get_push_sender()

    @property
    def config(self) -> A2AChannelConfig:
        """Get the channel configuration."""
        return _get_config()


# Export for convenience
a2a_routes = enhanced_a2a_routes
