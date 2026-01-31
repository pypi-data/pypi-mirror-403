"""
mia-anemoi: Agent-to-Agent Communication Library
A Python client library for Anemoi A2A communication patterns.

This is Mia's fork of Coral-Protocol/Anemoi, adapted for terminal-based
agent orchestration and SimExp integration.

Features:
- Thread-based A2A messaging via MCP server
- File-based transport for local development
- Session genealogy tracking
- Context inheritance on fork/resume
"""

__version__ = "0.1.0"
__author__ = "Mia Isabelle"

from .client import AnemoiClient, AnemoiClientConfig
from .messages import (
    AnemoiMessage,
    AnemoiMessageType,
    SessionGenealogy,
    create_spawn_message,
    create_ready_message,
    create_update_message,
    create_wisdom_broadcast,
)
from .transport import (
    FileTransport,
    MCPTransport,
    Transport,
)

__all__ = [
    # Client
    "AnemoiClient",
    "AnemoiClientConfig",
    # Messages
    "AnemoiMessage",
    "AnemoiMessageType",
    "SessionGenealogy",
    "create_spawn_message",
    "create_ready_message",
    "create_update_message",
    "create_wisdom_broadcast",
    # Transport
    "Transport",
    "FileTransport",
    "MCPTransport",
]
