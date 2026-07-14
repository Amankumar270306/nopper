"""Nopper SDK v2 — unified interface to manage all AI providers."""

from nopper.agent import Agent, Tool, tool
from nopper.conversation import AsyncConversation, Conversation
from nopper.errors import NopperError
from nopper.models import (
    AIString,
    ArenaResponse,
    ChatResponse,
    Message,
    Role,
    StreamChunk,
)
from nopper.node import Node, NodeConfig, NodeManager
from nopper.wrapper import AI, AsyncAI, Middleware, MiddlewarePipeline

__version__ = "0.2.0"

__all__ = [
    "AI",
    "AIString",
    "Agent",
    "ArenaResponse",
    "AsyncAI",
    "AsyncConversation",
    "ChatResponse",
    "Conversation",
    "Message",
    "Middleware",
    "MiddlewarePipeline",
    "Node",
    "NodeConfig",
    "NodeManager",
    "NopperError",
    "Role",
    "StreamChunk",
    "Tool",
    "tool",
]
