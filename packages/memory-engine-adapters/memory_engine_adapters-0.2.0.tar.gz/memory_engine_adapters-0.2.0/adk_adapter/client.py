"""Compatibility wrapper for client symbols."""

from memory_engine_adapters.adk_adapter.client import (  # noqa: F401
    AuthenticationError,
    AuthorizationError,
    MemoryEngineClient,
    MemoryEngineError,
    MemoryItem,
    Message,
    ProviderUnavailableError,
    RateLimitError,
    Scope,
    ValidationError,
)

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "MemoryEngineClient",
    "MemoryEngineError",
    "MemoryItem",
    "Message",
    "ProviderUnavailableError",
    "RateLimitError",
    "Scope",
    "ValidationError",
]
