"""MCP (Model Context Protocol) channel with dual-mode support.

This module provides MCP Streamable HTTP transport endpoints with two modes:

1. Multi-tool mode (/mcp):
   - Exposes ALL Assistants as individual tools
   - Suitable for AI clients that want to discover and use multiple agents
   - Uses existing api/mcp.py implementation

2. Single-tool mode (/mcp/{assistant_id}):
   - Exposes ONE specific Assistant as a tool with full MCP features
   - Supports streaming responses (SSE)
   - Supports session management (Mcp-Session-Id)
   - Supports progress notifications

MCP Protocol specification:
https://modelcontextprotocol.io/specification/2025-03-26/basic/transports

Endpoints:
    Multi-tool mode:
    - POST /mcp                             JSON-RPC (all assistants as tools)

    Single-tool mode:
    - GET  /mcp/{assistant_id}/health       Health check
    - POST /mcp/{assistant_id}              JSON-RPC (single assistant, streaming support)
    - GET  /mcp/{assistant_id}              SSE stream for server-initiated messages
"""

import functools
import uuid
from typing import Any, Literal, NotRequired

import orjson
import structlog
from langgraph_sdk.client import LangGraphClient, get_client
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute
from typing_extensions import TypedDict

from orcakit_api import __version__
from orcakit_api.api.mcp import mcp_routes as multi_assistant_routes
from orcakit_api.channels.base import BaseChannel
from orcakit_api.route import ApiRequest, ApiRoute
from orcakit_api.sse import EventSourceResponse

logger = structlog.stdlib.get_logger(__name__)


# ============================================================================
# Constants and Configuration
# ============================================================================

MCP_PROTOCOL_VERSION = "2024-11-05"

# JSON-RPC error codes
ERROR_CODE_PARSE_ERROR = -32700
ERROR_CODE_INVALID_REQUEST = -32600
ERROR_CODE_METHOD_NOT_FOUND = -32601
ERROR_CODE_INVALID_PARAMS = -32602
ERROR_CODE_INTERNAL_ERROR = -32603


# ============================================================================
# Type Definitions
# ============================================================================


class JsonRpcErrorObject(TypedDict):
    code: int
    message: str
    data: NotRequired[Any]


class JsonRpcRequest(TypedDict):
    jsonrpc: Literal["2.0"]
    id: str | int
    method: str
    params: NotRequired[dict[str, Any]]


class JsonRpcResponse(TypedDict):
    jsonrpc: Literal["2.0"]
    id: str | int
    result: NotRequired[dict[str, Any]]
    error: NotRequired[JsonRpcErrorObject]


class JsonRpcNotification(TypedDict):
    jsonrpc: Literal["2.0"]
    method: str
    params: NotRequired[dict[str, Any]]


class MCPToolInputSchema(TypedDict):
    """Input schema for MCP tool."""

    type: str
    properties: dict[str, Any]
    required: list[str]


class MCPTool(TypedDict):
    """MCP tool definition."""

    name: str
    description: str
    inputSchema: MCPToolInputSchema


# ============================================================================
# Helper Functions
# ============================================================================


@functools.lru_cache(maxsize=1)
def _client() -> LangGraphClient:
    """Get a client for local operations."""
    return get_client(url=None)


def _create_jsonrpc_response(id_: int | str | None, result: Any) -> dict[str, Any]:
    """Create a JSON-RPC 2.0 success response."""
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _create_jsonrpc_error(
    id_: int | str | None, code: int, message: str, data: Any = None
) -> dict[str, Any]:
    """Create a JSON-RPC 2.0 error response."""
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": error}


async def _get_assistant(
    assistant_id: str, headers: dict[str, Any] | None
) -> dict[str, Any]:
    """Get assistant with proper 404 error handling."""
    try:
        return await get_client().assistants.get(assistant_id, headers=headers)
    except Exception as e:
        if (
            hasattr(e, "response")
            and hasattr(e.response, "status_code")
            and e.response.status_code == 404
        ):
            raise ValueError(f"Assistant '{assistant_id}' not found") from e
        raise ValueError(f"Failed to get assistant '{assistant_id}': {e}") from e


def _get_tool_input_schema() -> MCPToolInputSchema:
    """Get the JSON Schema for tool input."""
    return {
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {
                            "type": "string",
                            "enum": ["user", "assistant", "system"],
                            "description": "Message role",
                        },
                        "content": {
                            "type": "string",
                            "description": "Message content",
                        },
                    },
                    "required": ["role", "content"],
                },
                "description": "List of messages with role and content",
            },
            "thread_id": {
                "type": "string",
                "description": "Thread ID for conversation continuity",
            },
        },
        "required": ["messages"],
    }


def _extract_response_text(result: dict[str, Any]) -> str:
    """Extract text response from LangGraph result."""
    if "__error__" in result:
        error_info = result.get("__error__", {})
        return f"Error: {error_info.get('error', 'Unknown error')}"

    messages = result.get("messages", [])
    if isinstance(messages, list) and messages:
        for message in reversed(messages):
            if isinstance(message, dict):
                msg_type = message.get("type", "")
                msg_role = message.get("role", "")
                if msg_type == "ai" or msg_role == "assistant":
                    content = message.get("content", "")
                    if isinstance(content, str):
                        return content

        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            return str(last_msg.get("content", ""))

    return str(result)


# ============================================================================
# Single Assistant Mode - Endpoint Handlers
# ============================================================================


async def handle_single_health(request: ApiRequest) -> Response:
    """Health check endpoint for single assistant mode."""
    assistant_id = request.path_params.get("assistant_id", "")
    return JSONResponse({
        "status": "healthy",
        "protocol": "mcp",
        "transport": "streamable-http",
        "mode": "single-assistant",
        "assistant_id": assistant_id,
    })


async def handle_single_post(request: ApiRequest) -> Response:
    """Handle MCP POST request for single assistant.

    Supports:
    - initialize: Initialize MCP session
    - tools/list: List available tools (returns single tool for this assistant)
    - tools/call: Execute the assistant (supports streaming via SSE)
    """
    assistant_id = request.path_params.get("assistant_id")
    if not assistant_id:
        return JSONResponse(
            {"error": "Missing assistant_id in URL path"},
            status_code=400,
        )

    try:
        body = await request.body()
        message = orjson.loads(body)
    except orjson.JSONDecodeError:
        return JSONResponse(
            _create_jsonrpc_error(None, ERROR_CODE_PARSE_ERROR, "Parse error"),
            status_code=400,
        )

    # Validate JSON-RPC format
    if not isinstance(message, dict):
        return JSONResponse(
            _create_jsonrpc_error(None, ERROR_CODE_INVALID_REQUEST, "Invalid message format"),
            status_code=400,
        )

    if message.get("jsonrpc") != "2.0":
        return JSONResponse(
            _create_jsonrpc_error(
                message.get("id"),
                ERROR_CODE_INVALID_REQUEST,
                "Invalid JSON-RPC version",
            ),
            status_code=400,
        )

    # Handle batch requests
    if isinstance(message, list):
        return await _handle_batch_request(request, message, assistant_id)

    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params", {})

    # Check if it's a notification (no id)
    if method and request_id is None:
        await _process_notification(message)
        return Response(status_code=202)

    # Check if it's a response (has result or error but no method)
    if method is None and ("result" in message or "error" in message):
        return Response(status_code=202)

    # Check if streaming is requested for tools/call
    accept = request.headers.get("Accept", "")
    if "text/event-stream" in accept and method == "tools/call":
        return await _handle_streaming_tools_call(request, message, assistant_id)

    # Handle regular JSON-RPC request
    try:
        if method == "initialize":
            result = _handle_initialize(request_id)
        elif method == "tools/list":
            result = await _handle_tools_list(request, request_id, assistant_id)
        elif method == "tools/call":
            result = await _handle_tools_call(request, request_id, params, assistant_id)
        elif method == "ping":
            result = _create_jsonrpc_response(request_id, {})
        else:
            result = _create_jsonrpc_error(
                request_id, ERROR_CODE_METHOD_NOT_FOUND, f"Method not found: {method}"
            )

        # Add session header for initialize
        headers = {}
        session_id = request.headers.get("Mcp-Session-Id")
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        elif method == "initialize":
            headers["Mcp-Session-Id"] = str(uuid.uuid4())

        return JSONResponse(result, headers=headers)

    except Exception as e:
        await logger.aexception("Error processing MCP request", method=method, error=str(e))
        return JSONResponse(
            _create_jsonrpc_error(request_id, ERROR_CODE_INTERNAL_ERROR, str(e)),
            status_code=500,
        )


async def handle_single_get(request: ApiRequest) -> Response:
    """Handle MCP GET request for SSE stream.

    Opens an SSE stream for server-initiated messages.
    """
    accept = request.headers.get("Accept", "")
    if "text/event-stream" not in accept:
        return Response(status_code=405, content="Method Not Allowed")

    async def sse_stream():
        # Keep-alive stream for server-initiated messages
        yield (b"event", "ping")
        yield (b"data", {})

    return EventSourceResponse(
        sse_stream(),
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Single Assistant Mode - JSON-RPC Method Handlers
# ============================================================================


def _handle_initialize(request_id: int | str | None) -> dict[str, Any]:
    """Handle initialize request."""
    return _create_jsonrpc_response(
        request_id,
        {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": "orcakit-mcp-server",
                "version": __version__,
            },
        },
    )


async def _handle_tools_list(
    request: ApiRequest, request_id: int | str | None, assistant_id: str
) -> dict[str, Any]:
    """Handle tools/list request for single assistant."""
    try:
        assistant = await _get_assistant(assistant_id, request.headers)
        description = assistant.get("description") or f"Execute assistant {assistant.get('name', assistant_id)}"

        tool: MCPTool = {
            "name": assistant.get("name", assistant_id),
            "description": description,
            "inputSchema": _get_tool_input_schema(),
        }

        return _create_jsonrpc_response(request_id, {"tools": [tool]})

    except ValueError as e:
        return _create_jsonrpc_error(request_id, ERROR_CODE_INVALID_PARAMS, str(e))


async def _handle_tools_call(
    request: ApiRequest,
    request_id: int | str | None,
    params: dict[str, Any],
    assistant_id: str,
) -> dict[str, Any]:
    """Handle tools/call request for single assistant (non-streaming)."""
    client = _client()
    arguments = params.get("arguments", {})
    messages = arguments.get("messages", [])
    thread_id = arguments.get("thread_id") or str(uuid.uuid4())

    if not messages:
        return _create_jsonrpc_error(
            request_id, ERROR_CODE_INVALID_PARAMS, "Missing 'messages' in arguments"
        )

    try:
        # Convert messages to LangGraph format
        langgraph_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                langgraph_messages.append({"role": "system", "content": content})
            elif role == "assistant":
                langgraph_messages.append({"role": "ai", "content": content})
            else:
                langgraph_messages.append({"role": "human", "content": content})

        result = await client.runs.wait(
            thread_id=thread_id,
            assistant_id=assistant_id,
            input={"messages": langgraph_messages},
            if_not_exists="create",
            raise_error=False,
            headers=request.headers,
        )

        if "__error__" in result:
            return _create_jsonrpc_response(
                request_id,
                {
                    "content": [{"type": "text", "text": result["__error__"]["error"]}],
                    "isError": True,
                },
            )

        response_text = _extract_response_text(result)
        return _create_jsonrpc_response(
            request_id,
            {
                "content": [{"type": "text", "text": response_text}],
                "isError": False,
            },
        )

    except Exception as e:
        await logger.aexception("Error in tools/call", assistant_id=assistant_id, error=str(e))
        return _create_jsonrpc_response(
            request_id,
            {
                "content": [{"type": "text", "text": str(e)}],
                "isError": True,
            },
        )


async def _handle_streaming_tools_call(
    request: ApiRequest,
    message: dict[str, Any],
    assistant_id: str,
) -> Response:
    """Handle tools/call with SSE streaming response."""
    client = _client()
    request_id = message.get("id")
    params = message.get("params", {})
    arguments = params.get("arguments", {})
    messages = arguments.get("messages", [])
    thread_id = arguments.get("thread_id") or str(uuid.uuid4())

    async def sse_generator():
        event_id = 0

        if not messages:
            error_response = _create_jsonrpc_error(
                request_id, ERROR_CODE_INVALID_PARAMS, "Missing 'messages' in arguments"
            )
            yield (b"id", str(event_id))
            yield (b"event", "message")
            yield (b"data", error_response)
            return

        try:
            # Convert messages to LangGraph format
            langgraph_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    langgraph_messages.append({"role": "system", "content": content})
                elif role == "assistant":
                    langgraph_messages.append({"role": "ai", "content": content})
                else:
                    langgraph_messages.append({"role": "human", "content": content})

            # Create streaming run
            run = await client.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                input={"messages": langgraph_messages},
                stream_mode=["messages"],
                if_not_exists="create",
                headers=request.headers,
            )

            accumulated_content = ""

            stream = client.runs.join_stream(
                run_id=run["run_id"],
                thread_id=run["thread_id"],
                headers=request.headers,
            )

            async for chunk in stream:
                try:
                    if chunk.event.startswith("messages"):
                        items = chunk.data or []
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    content = item.get("content", "")
                                    if content:
                                        accumulated_content += str(content)
                                        # Send progress notification
                                        progress: JsonRpcNotification = {
                                            "jsonrpc": "2.0",
                                            "method": "notifications/progress",
                                            "params": {
                                                "progressToken": request_id,
                                                "progress": len(accumulated_content),
                                                "data": {"chunk": str(content)},
                                            },
                                        }
                                        yield (b"id", str(event_id))
                                        yield (b"event", "message")
                                        yield (b"data", progress)
                                        event_id += 1
                except Exception as e:
                    await logger.aexception("Error processing stream chunk", error=str(e))
                    continue

            # Send final response
            final_response = _create_jsonrpc_response(
                request_id,
                {
                    "content": [{"type": "text", "text": accumulated_content}],
                    "isError": False,
                },
            )
            yield (b"id", str(event_id))
            yield (b"event", "message")
            yield (b"data", final_response)

        except Exception as e:
            await logger.aexception("Error in streaming tools/call", assistant_id=assistant_id, error=str(e))
            error_response = _create_jsonrpc_response(
                request_id,
                {
                    "content": [{"type": "text", "text": str(e)}],
                    "isError": True,
                },
            )
            yield (b"id", str(event_id))
            yield (b"event", "message")
            yield (b"data", error_response)

    session_id = request.headers.get("Mcp-Session-Id")
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id

    return EventSourceResponse(sse_generator(), headers=headers)


async def _handle_batch_request(
    request: ApiRequest,
    requests: list[dict[str, Any]],
    assistant_id: str,
) -> Response:
    """Handle batch JSON-RPC requests."""
    responses = []
    has_requests = False

    for req in requests:
        if not isinstance(req, dict):
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method and req_id is not None:
            has_requests = True
            if method == "initialize":
                result = _handle_initialize(req_id)
            elif method == "tools/list":
                result = await _handle_tools_list(request, req_id, assistant_id)
            elif method == "tools/call":
                result = await _handle_tools_call(request, req_id, params, assistant_id)
            elif method == "ping":
                result = _create_jsonrpc_response(req_id, {})
            else:
                result = _create_jsonrpc_error(
                    req_id, ERROR_CODE_METHOD_NOT_FOUND, f"Method not found: {method}"
                )
            responses.append(result)
        elif method:
            # Notification - no response needed
            await _process_notification(req)

    if not has_requests:
        return Response(status_code=202)

    return JSONResponse(responses)


async def _process_notification(notification: dict[str, Any]) -> None:
    """Process a JSON-RPC notification."""
    method = notification.get("method")
    await logger.adebug("Received MCP notification", method=method)

    if method == "notifications/initialized":
        await logger.ainfo("MCP client initialized")
    elif method == "notifications/cancelled":
        await logger.ainfo("MCP request cancelled", params=notification.get("params", {}))


# ============================================================================
# Route Definitions
# ============================================================================

# Single assistant routes (must be defined before multi-assistant routes to avoid path conflicts)
single_assistant_routes = [
    ApiRoute("/mcp/{assistant_id}/health", handle_single_health, methods=["GET"]),
    ApiRoute("/mcp/{assistant_id}", handle_single_post, methods=["POST"]),
    ApiRoute("/mcp/{assistant_id}", handle_single_get, methods=["GET"]),
]

# Combined routes: single assistant routes first, then multi-assistant routes
mcp_routes = single_assistant_routes + multi_assistant_routes


# ============================================================================
# Channel Class
# ============================================================================


class MCPChannel(BaseChannel):
    """MCP (Model Context Protocol) channel with dual-mode support.

    This channel provides two modes of operation:

    1. Multi-tool mode (/mcp):
       - Exposes all Assistants as individual tools
       - Suitable for AI clients that want to discover and use multiple agents
       - JSON responses only

    2. Single-tool mode (/mcp/{assistant_id}):
       - Exposes one specific Assistant as a tool
       - Full MCP features: streaming (SSE), session management, progress notifications
       - Suitable for dedicated agent integration

    Example:
        >>> from orcakit_api.channels import MCPChannel
        >>> channel = MCPChannel()
        >>> print(channel.name)  # "mcp"
        >>> print(channel.routes)  # List of routes

    Claude Desktop configuration (multi-tool):
        {
            "mcpServers": {
                "all-agents": {"url": "http://localhost:8000/mcp"}
            }
        }

    Claude Desktop configuration (single-tool with streaming):
        {
            "mcpServers": {
                "my-agent": {"url": "http://localhost:8000/mcp/assistant-id"}
            }
        }
    """

    @property
    def name(self) -> str:
        """Return the channel name."""
        return "mcp"

    @property
    def routes(self) -> list[BaseRoute]:
        """Return the list of routes for this channel."""
        return mcp_routes
