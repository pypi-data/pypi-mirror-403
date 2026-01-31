"""WeWork channel for exposing LangGraph apps through WeWork robot protocol.

This module provides endpoints compatible with WeWork (企业微信) robot message format,
allowing LangGraph assistants to be used as WeWork chatbots.

Endpoints:
    - GET  /wework/health              Health check
    - POST /wework/call/{assistant_id} Synchronous chat call
    - POST /wework/stream/{assistant_id} Streaming chat response
"""

import functools
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


class WeWorkChatRequest(TypedDict):
    """WeWork chat request model."""

    content: str  # The user message content
    msg_id: NotRequired[str]  # Message ID
    user: NotRequired[str]  # User identifier
    msg_type: NotRequired[str]  # Message type, default "text"
    raw_msg: NotRequired[str]  # Raw XML message
    session_id: NotRequired[str | None]  # Session ID for conversation continuity
    business_keys: NotRequired[list[str]]  # Business keys
    request_source: NotRequired[str]  # Request source, default "robot"
    stream: NotRequired[bool]  # Enable streaming response


class WeWorkGlobalOutput(TypedDict):
    """WeWork global output model."""

    urls: NotRequired[str]  # Related URLs
    context: NotRequired[str]  # Context information
    answer_success: NotRequired[int]  # Answer success flag (0 or 1)
    docs: NotRequired[list[str]]  # Related documents


class WeWorkStreamResponse(TypedDict):
    """WeWork streaming response model."""

    response: str  # Response content
    finished: bool  # Whether response is finished
    global_output: WeWorkGlobalOutput  # Global output information


class WeWorkChatResponse(TypedDict):
    """WeWork chat response model for non-streaming."""

    response: str  # Response content
    session_id: str  # Session ID
    global_output: WeWorkGlobalOutput  # Global output information


# ============================================================================
# Helper Functions
# ============================================================================


@functools.lru_cache(maxsize=1)
def _client() -> LangGraphClient:
    """Get a client for local operations."""
    return get_client(url=None)


def _coerce_content_text(content: Any) -> str:
    """Coerce various content shapes to a text string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif "content" in item:
                    parts.append(str(item["content"]))
        return "".join(parts) if parts else str(content)
    if isinstance(content, dict):
        if "text" in content:
            return str(content["text"])
        if "content" in content:
            return str(content["content"])
    return str(content)


def _extract_content_from_response(content: Any) -> str:
    """Return raw content text without special JSON/match_tools handling."""
    if content is None:
        return ""
    return _coerce_content_text(content)


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
                    return _extract_content_from_response(content)

        # Fallback to last message content
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            return _extract_content_from_response(last_msg.get("content", ""))

    # Fallback to string representation
    return str(result)


def _create_global_output(answer_success: int = 0) -> WeWorkGlobalOutput:
    """Create a default global output object."""
    return {
        "urls": "",
        "context": "",
        "answer_success": answer_success,
        "docs": [],
    }


# ============================================================================
# Endpoint Handlers
# ============================================================================


async def handle_health(request: ApiRequest) -> Response:
    """Health check endpoint.

    Returns:
        JSON response with health status
    """
    return JSONResponse({"status": "healthy"})


async def handle_call(request: ApiRequest) -> Response:
    """Handle synchronous chat call.

    Expected URL: /wework/call/{assistant_id}

    Request body (JSON):
        {
            "content": "Hello",
            "user": "user-123",
            "msg_id": "msg-456",
            "session_id": "session-789"
        }

    Returns:
        WeWork chat response with the assistant's reply
    """
    client = _client()
    assistant_id = request.path_params.get("assistant_id")

    if not assistant_id:
        return JSONResponse(
            {"error": "Missing assistant_id in URL path"},
            status_code=400,
        )

    try:
        body = await request.body()
        if not body or body.strip() == b"":
            # 空请求返回 200 和默认响应
            response: WeWorkChatResponse = {
                "response": "",
                "session_id": "",
                "global_output": _create_global_output(answer_success=1),
            }
            return JSONResponse(response, status_code=200)
        params: WeWorkChatRequest = orjson.loads(body)
    except orjson.JSONDecodeError:
        return JSONResponse(
            {"error": "Invalid JSON in request body"},
            status_code=400,
        )

    content = params.get("content", "")
    if not content:
        # 空 content 也返回 200
        response: WeWorkChatResponse = {
            "response": "",
            "session_id": "",
            "global_output": _create_global_output(answer_success=1),
        }
        return JSONResponse(response, status_code=200)

    user = params.get("user", "")
    session_id = params.get("session_id")
    thread_id = session_id if session_id else str(uuid.uuid4())

    await logger.ainfo(
        "WeWork call request",
        assistant_id=assistant_id,
        user=user,
        msg_id=params.get("msg_id", ""),
        thread_id=thread_id,
    )

    try:
        # Create input in LangChain message format
        input_content = {
            "messages": [{"role": "human", "content": content}],
        }

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

        response: WeWorkChatResponse = {
            "response": response_text,
            "session_id": thread_id,
            "global_output": _create_global_output(answer_success=1),
        }

        return JSONResponse(response)

    except Exception as e:
        await logger.aexception(
            "Error in WeWork call endpoint",
            assistant_id=assistant_id,
            error=str(e),
        )
        return JSONResponse(
            {
                "error": str(e),
                "detail": "Failed to process chat request",
            },
            status_code=500,
        )


async def handle_stream(request: ApiRequest) -> Response:
    """Handle streaming chat response.

    Expected URL: /wework/stream/{assistant_id}

    Request body (JSON):
        {
            "content": "Hello",
            "user": "user-123",
            "session_id": "session-789"
        }

    Returns:
        Server-Sent Events stream with WeWork response format
    """
    client = _client()
    assistant_id = request.path_params.get("assistant_id")

    if not assistant_id:
        return JSONResponse(
            {"error": "Missing assistant_id in URL path"},
            status_code=400,
        )

    try:
        body = await request.body()
        if not body or body.strip() == b"":
            # 空请求返回 200 和默认响应
            response: WeWorkChatResponse = {
                "response": "",
                "session_id": "",
                "global_output": _create_global_output(answer_success=1),
            }
            return JSONResponse(response, status_code=200)
        params: WeWorkChatRequest = orjson.loads(body)
    except orjson.JSONDecodeError:
        return JSONResponse(
            {"error": "Invalid JSON in request body"},
            status_code=400,
        )

    content = params.get("content", "")
    if not content:
        # 空 content 也返回 200
        response: WeWorkChatResponse = {
            "response": "",
            "session_id": "",
            "global_output": _create_global_output(answer_success=1),
        }
        return JSONResponse(response, status_code=200)

    user = params.get("user", "")
    session_id = params.get("session_id")
    thread_id = session_id if session_id else str(uuid.uuid4())

    await logger.ainfo(
        "WeWork stream request",
        assistant_id=assistant_id,
        user=user,
        thread_id=thread_id,
    )

    async def stream_body():
        """Generate SSE stream with WeWork response format."""
        # 记录上一次的累积内容，用于计算增量
        previous_content = ""
        # 记录完整的响应内容（用于最终消息）
        full_response = ""
        
        try:
            # Create input in LangChain message format
            input_content = {
                "messages": [{"role": "human", "content": content}],
            }

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
                                    # 只处理 AI 消息类型
                                    item_type = item.get("type", "")
                                    item_role = item.get("role", "")
                                    if item_type != "ai" and item_role != "assistant":
                                        continue
                                    
                                    metadata = item.get("metadata") if isinstance(item, dict) else None
                                    if isinstance(metadata, dict):
                                        node_name = metadata.get("langgraph_node")
                                        if node_name == "tool_matcher":
                                            continue
                                    item_content = item.get("content", "")
                                    # 过滤掉 {"match_tools": [...]} 等 JSON 前缀
                                    current_content = _extract_content_from_response(item_content)
                                    # 如果过滤后为空，跳过
                                    if not current_content:
                                        continue
                                    # 上游返回的 content 是累积的完整内容
                                    # 计算增量：新内容 - 上次内容 = 本次新增的部分
                                    if current_content.startswith(previous_content):
                                        # 计算新增的部分
                                        delta = current_content[len(previous_content):]
                                    else:
                                        # 如果不是前缀关系，说明内容被重置，发送完整内容
                                        delta = current_content
                                    
                                    # 更新记录
                                    previous_content = current_content
                                    full_response = current_content
                                    
                                    # 只有有新增内容时才发送
                                    if delta:
                                        response: WeWorkStreamResponse = {
                                            "response": delta,  # 只发送增量内容
                                            "finished": False,
                                            "global_output": _create_global_output(),
                                        }
                                        yield (b"data", response)
                except Exception as e:
                    await logger.aexception(
                        "Error processing stream chunk", error=str(e)
                    )
                    continue

        except Exception as e:
            await logger.aexception(
                "WeWork stream error",
                assistant_id=assistant_id,
                error=str(e),
            )
            error_response = {"error": str(e)}
            yield (b"data", error_response)

        finally:
            # Send final message with empty content (all content already sent as deltas)
            final_response: WeWorkStreamResponse = {
                "response": "",  # 增量模式下，最后发送空内容表示结束
                "finished": True,
                "global_output": _create_global_output(answer_success=1),
            }
            yield (b"data", final_response)
            await logger.ainfo("WeWork stream finished", thread_id=thread_id, full_response_length=len(full_response))

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

wework_routes = [
    ApiRoute("/wework/health", handle_health, methods=["GET"]),
    ApiRoute("/wework/call/{assistant_id}", handle_call, methods=["POST"]),
    ApiRoute("/wework/stream/{assistant_id}", handle_stream, methods=["POST"]),
]


# ============================================================================
# Channel Class
# ============================================================================


class WeWorkChannel(BaseChannel):
    """WeWork channel implementation.

    This channel exposes LangGraph assistants through WeWork robot protocol,
    allowing them to be used as WeWork chatbots.

    Example:
        >>> from orcakit_api.channels import WeWorkChannel
        >>> channel = WeWorkChannel()
        >>> print(channel.name)  # "wework"
        >>> print(channel.routes)  # List of routes
    """

    @property
    def name(self) -> str:
        """Return the channel name."""
        return "wework"

    @property
    def routes(self) -> list[BaseRoute]:
        """Return the list of routes for this channel."""
        return wework_routes
