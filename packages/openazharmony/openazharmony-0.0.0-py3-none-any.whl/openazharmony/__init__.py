# OpenAI and Azure compatibility helpers with response format contracts.

from __future__ import annotations

from .client import HarmonyClient, build_chat_messages, build_responses_input
from .contracts import (
    ClientConfig,
    JsonSchemaSpec,
    ResponseFormat,
    JsonObj,
    ToolChoice,
    normalize_response_format,
)

__version__ = "0.0.0"

__all__ = [
    "ClientConfig",
    "HarmonyClient",
    "JsonSchemaSpec",
    "ResponseFormat",
    "JsonObj",
    "ToolChoice",
    "build_chat_messages",
    "build_responses_input",
    "normalize_response_format",
    "__version__",
]
