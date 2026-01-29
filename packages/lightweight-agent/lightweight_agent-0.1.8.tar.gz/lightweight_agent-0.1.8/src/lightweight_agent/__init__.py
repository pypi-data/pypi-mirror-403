"""Lightweight Agent - LLM Client Library"""
from .clients.openai_client import OpenAIClient
from .clients.base import BaseClient
from .exceptions import (
    LLMClientError,
    ConfigurationError,
    APIError,
    NetworkError,
    ValidationError
)
from .models import TokenUsage, GenerateResponse, StreamingResponse
from .agent import ReActAgent, TodoBasedAgent, build_system_prompt, CitationAgent, FigureAgent
from .session.session import Session
from .tools.registry import ToolRegistry
from .tools.base import Tool
from .utils import (
    encode_image_to_base64,
    create_openai_image_message,
    create_anthropic_image_message
)

# Optional dependency: anthropic
try:
    from .clients.anthropic_client import AnthropicClient  # type: ignore
except Exception:  # pragma: no cover
    AnthropicClient = None  # type: ignore

__version__ = "0.1.7"
__all__ = [
    "OpenAIClient",
    "AnthropicClient",
    "BaseClient",
    "LLMClientError",
    "ConfigurationError",
    "APIError",
    "NetworkError",
    "ValidationError",
    "TokenUsage",
    "GenerateResponse",
    "StreamingResponse",
    "ReActAgent",
    "TodoBasedAgent",
    "CitationAgent",
    "FigureAgent",
    "build_system_prompt",
    "Session",
    "ToolRegistry",
    "Tool",
    "encode_image_to_base64",
    "create_openai_image_message",
    "create_anthropic_image_message",
]

