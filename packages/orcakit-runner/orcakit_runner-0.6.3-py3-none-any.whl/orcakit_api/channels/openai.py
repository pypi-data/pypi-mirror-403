"""OpenAI-compatible channel for exposing LangGraph apps through OpenAI API protocol.

This module provides endpoints compatible with OpenAI Chat Completions API,
allowing LangGraph assistants to be used as OpenAI-compatible models.

Endpoints:
    - GET  /openai/health                              Health check
    - GET  /openai/v1/models                           List available models
    - POST /openai/v1/chat/completions/{assistant_id}  Chat completions
"""

import functools
import time
import uuid
from typing import Any, NotRequired

import orjson
import structlog
from langgraph_sdk.client import LangGraphClient, get_client
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute
from typing_extensions import TypedDict

from orcakit_api.channels.base import BaseChannel
from orcakit_api.route import ApiRequest, ApiRoute
from orcakit_api.sse import EventSourceResponse

logger = structlog.stdlib.get_logger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================


class ChatMessage(TypedDict):
    """OpenAI-compatible chat message."""

    role: str
    content: str
    name: NotRequired[str]


class ChatCompletionRequest(TypedDict):
    """OpenAI-compatible chat completion request."""

    model: str
    messages: list[ChatMessage]
    temperature: NotRequired[float]
    top_p: NotRequired[float]
    n: NotRequired[int]
    stream: NotRequired[bool]
    stop: NotRequired[list[str]]
    max_tokens: NotRequired[int]
    presence_penalty: NotRequired[float]
    frequency_penalty: NotRequired[float]
    logit_bias: NotRequired[dict[str, float]]
    user: NotRequired[str]


class ChatCompletionResponseChoice(TypedDict):
    """OpenAI-compatible chat completion response choice."""

    index: int
    message: ChatMessage
    finish_reason: str


class UsageInfo(TypedDict):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(TypedDict):
    """OpenAI-compatible chat completion response."""

    id: str
    object: str
    created: int
    model: str
    choices: list[ChatCompletionResponseChoice]
    usage: UsageInfo


class DeltaContent(TypedDict, total=False):
    """Delta content for streaming response."""

    content: str
    role: str
    tool_calls: list[dict[str, Any]]


class StreamChoice(TypedDict):
    """Streaming response choice."""

    index: int
    delta: DeltaContent
    finish_reason: str | None


class ChatCompletionChunk(TypedDict):
    """OpenAI-compatible chat completion chunk for streaming."""

    id: str
    object: str
    created: int
    model: str
    choices: list[StreamChoice]


class ModelInfo(TypedDict):
    """Model information."""

    id: str
    object: str
    created: int
    owned_by: str


class ModelListResponse(TypedDict):
    """Model list response."""

    object: str
    data: list[ModelInfo]


# ============================================================================
# Helper Functions
# ============================================================================


@functools.lru_cache(maxsize=1)
def _client() -> LangGraphClient:
    """Get a client for local operations."""
    return get_client(url=None)


def _extract_response_text(result: dict[str, Any]) -> str:
    """Extract text response from LangGraph result.

    Args:
        result: The result from LangGraph execution

    Returns:
        The extracted text content
    """
    if "__error__" in result:
        error_info = result.get("__error__", {})
        return f"Error: {error_info.get('error', 'Unknown error')}"

    # Try to extract from messages
    messages = result.get("messages", [])
    if isinstance(messages, list) and messages:
        # Find the last assistant/AI message
        for message in reversed(messages):
            if isinstance(message, dict):
                msg_type = message.get("type", "")
                msg_role = message.get("role", "")
                if msg_type == "ai" or msg_role == "assistant":
                    content = message.get("content", "")
                    if isinstance(content, str):
                        return content

        # Fallback to last message content
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            return str(last_msg.get("content", ""))

    # Fallback to string representation
    return str(result)


def _convert_messages_to_langgraph(messages: list[ChatMessage]) -> list[dict[str, str]]:
    """Convert OpenAI format messages to LangGraph format.

    Args:
        messages: List of OpenAI-format chat messages.

    Returns:
        List of LangGraph message dicts.
    """
    converted: list[dict[str, str]] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # Map OpenAI roles to LangGraph roles
        if role == "system":
            converted.append({"role": "system", "content": content})
        elif role == "assistant":
            converted.append({"role": "ai", "content": content})
        else:
            # user or unknown roles treated as human
            converted.append({"role": "human", "content": content})

    return converted


def _create_usage_info() -> UsageInfo:
    """Create default usage info (token counts not available from LangGraph)."""
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }


def _filter_none_values(d: dict[str, Any]) -> dict[str, Any]:
    """Filter out None values and empty strings from dict for JSON serialization."""
    return {k: v for k, v in d.items() if v is not None and v != ""}


# ============================================================================
# Endpoint Handlers
# ============================================================================


async def handle_health(request: ApiRequest) -> Response:
    """Health check endpoint.

    Returns:
        JSON response with health status
    """
    return JSONResponse({"status": "healthy"})


async def handle_models(request: ApiRequest) -> Response:
    """List available models.

    Returns OpenAI-compatible model list. Since we're proxying to LangGraph,
    we return a generic model entry. The actual assistant is specified in the URL.
    """
    model_info: ModelInfo = {
        "id": "langgraph-assistant",
        "object": "model",
        "created": int(time.time()),
        "owned_by": "orcakit",
    }

    response: ModelListResponse = {
        "object": "list",
        "data": [model_info],
    }

    return JSONResponse(response)


async def handle_chat_completions(request: ApiRequest) -> Response:
    """Handle chat completions request.

    Expected URL: /openai/v1/chat/completions/{assistant_id}

    Request body (JSON):
        {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": false
        }

    Returns:
        OpenAI-compatible chat completion response (streaming or non-streaming)
    """
    client = _client()
    assistant_id = request.path_params.get("assistant_id")

    if not assistant_id:
        return JSONResponse(
            {"error": {"message": "Missing assistant_id in URL path", "type": "invalid_request_error"}},
            status_code=400,
        )

    try:
        body = await request.body()
        params: ChatCompletionRequest = orjson.loads(body) if body else {}
    except orjson.JSONDecodeError:
        return JSONResponse(
            {"error": {"message": "Invalid JSON in request body", "type": "invalid_request_error"}},
            status_code=400,
        )

    messages = params.get("messages", [])
    if not messages:
        return JSONResponse(
            {"error": {"message": "Missing 'messages' field in request", "type": "invalid_request_error"}},
            status_code=400,
        )

    model = params.get("model", "langgraph-assistant")
    stream = params.get("stream", False)
    user = params.get("user", "")
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    thread_id = user if user else str(uuid.uuid4())

    await logger.ainfo(
        "OpenAI chat completions request",
        assistant_id=assistant_id,
        model=model,
        stream=stream,
        thread_id=thread_id,
        message_count=len(messages),
    )

    if stream:
        return await _handle_streaming_response(
            request, client, assistant_id, messages, model, completion_id, thread_id
        )
    else:
        return await _handle_non_streaming_response(
            request, client, assistant_id, messages, model, completion_id, thread_id
        )


async def _handle_non_streaming_response(
    request: ApiRequest,
    client: LangGraphClient,
    assistant_id: str,
    messages: list[ChatMessage],
    model: str,
    completion_id: str,
    thread_id: str,
) -> Response:
    """Handle non-streaming chat completion."""
    try:
        # Convert messages to LangGraph format
        langgraph_messages = _convert_messages_to_langgraph(messages)
        input_content = {"messages": langgraph_messages}

        # Execute the assistant
        result = await client.runs.wait(
            thread_id=thread_id,
            assistant_id=assistant_id,
            input=input_content,
            if_not_exists="create",
            raise_error=False,
            headers=request.headers,
        )

        response_text = _extract_response_text(result)

        response: ChatCompletionResponse = {
            "id": completion_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": response_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": _create_usage_info(),
        }

        return JSONResponse(response)

    except Exception as e:
        await logger.aexception(
            "Error in OpenAI chat completions endpoint",
            assistant_id=assistant_id,
            error=str(e),
        )
        return JSONResponse(
            {"error": {"message": str(e), "type": "server_error"}},
            status_code=500,
        )


async def _handle_streaming_response(
    request: ApiRequest,
    client: LangGraphClient,
    assistant_id: str,
    messages: list[ChatMessage],
    model: str,
    completion_id: str,
    thread_id: str,
) -> Response:
    """Handle streaming chat completion."""

    async def stream_body():
        """Generate SSE stream with OpenAI response format."""
        try:
            # Convert messages to LangGraph format
            langgraph_messages = _convert_messages_to_langgraph(messages)
            input_content = {"messages": langgraph_messages}

            # Send initial chunk with role
            initial_chunk: ChatCompletionChunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant"},
                        "finish_reason": None,
                    }
                ],
            }
            yield (b"data", _filter_none_values(initial_chunk))

            # Create run with streaming
            run = await client.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                input=input_content,
                stream_mode=["messages"],
                if_not_exists="create",
                headers=request.headers,
            )

            # Stream the response
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
                                    item_content = item.get("content", "")
                                    if item_content:
                                        content_chunk: ChatCompletionChunk = {
                                            "id": completion_id,
                                            "object": "chat.completion.chunk",
                                            "created": int(time.time()),
                                            "model": model,
                                            "choices": [
                                                {
                                                    "index": 0,
                                                    "delta": {"content": str(item_content)},
                                                    "finish_reason": None,
                                                }
                                            ],
                                        }
                                        yield (b"data", _filter_none_values(content_chunk))
                except Exception as e:
                    await logger.aexception(
                        "Error processing stream chunk", error=str(e)
                    )
                    continue

        except Exception as e:
            await logger.aexception(
                "OpenAI stream error",
                assistant_id=assistant_id,
                error=str(e),
            )
            error_chunk: ChatCompletionChunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": f"Error: {e}"},
                        "finish_reason": "error",
                    }
                ],
            }
            yield (b"data", _filter_none_values(error_chunk))

        finally:
            # Send final chunk with finish_reason
            final_chunk: ChatCompletionChunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            }
            yield (b"data", _filter_none_values(final_chunk))

            # Send [DONE] marker
            yield (b"data", "[DONE]")

            await logger.ainfo("OpenAI stream finished", thread_id=thread_id)

    return EventSourceResponse(
        stream_body(),
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Route Definitions
# ============================================================================

openai_routes = [
    ApiRoute("/openai/health", handle_health, methods=["GET"]),
    ApiRoute("/openai/v1/models", handle_models, methods=["GET"]),
    ApiRoute("/openai/v1/chat/completions/{assistant_id}", handle_chat_completions, methods=["POST"]),
]


# ============================================================================
# Channel Class
# ============================================================================


class OpenAIChannel(BaseChannel):
    """OpenAI-compatible channel implementation.

    This channel exposes LangGraph assistants through OpenAI-compatible API,
    allowing them to be used with any OpenAI client library.

    Example:
        >>> from orcakit_api.channels import OpenAIChannel
        >>> channel = OpenAIChannel()
        >>> print(channel.name)  # "openai"
        >>> print(channel.routes)  # List of routes

    Usage with OpenAI client:
        >>> from openai import OpenAI
        >>> client = OpenAI(base_url="http://localhost:8000/openai/v1", api_key="unused")
        >>> response = client.chat.completions.create(
        ...     model="my-assistant-id",  # assistant_id goes in model field
        ...     messages=[{"role": "user", "content": "Hello"}]
        ... )
    """

    @property
    def name(self) -> str:
        """Return the channel name."""
        return "openai"

    @property
    def routes(self) -> list[BaseRoute]:
        """Return the list of routes for this channel."""
        return openai_routes
