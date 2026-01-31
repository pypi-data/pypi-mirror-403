"""Channel implementations for different protocols.

This package contains channel implementations that expose LangGraph assistants
through various protocols and platforms.

Available Channels:
    - A2AChannel: A2A (Agent-to-Agent) protocol with enhanced features
    - MCPChannel: MCP (Model Context Protocol) with dual-mode support
    - OpenAIChannel: OpenAI-compatible API
    - WeWorkChannel: WeWork (企业微信) robot protocol

Future Channels:
    - LangGraphChannel: Standard LangGraph protocol
    - DingTalkChannel: DingTalk robot protocol
    - SlackChannel: Slack bot protocol
    - DiscordChannel: Discord bot protocol
"""

from orcakit_api.channels.a2a import A2AChannel, a2a_routes
from orcakit_api.channels.base import BaseChannel
from orcakit_api.channels.mcp import MCPChannel, mcp_routes
from orcakit_api.channels.openai import OpenAIChannel, openai_routes
from orcakit_api.channels.wework import WeWorkChannel, wework_routes

__all__ = [
    "A2AChannel",
    "a2a_routes",
    "BaseChannel",
    "MCPChannel",
    "mcp_routes",
    "OpenAIChannel",
    "openai_routes",
    "WeWorkChannel",
    "wework_routes",
]
