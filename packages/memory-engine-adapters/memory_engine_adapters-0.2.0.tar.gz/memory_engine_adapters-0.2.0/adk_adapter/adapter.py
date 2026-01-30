"""Compatibility wrapper for adapter symbols."""

from memory_engine_adapters.adk_adapter.adapter import (  # noqa: F401
    BaseMemoryService,
    MemoryEngineAdapter,
    MemoryResult,
    SearchMemoryResponse,
)

__all__ = [
    "BaseMemoryService",
    "MemoryEngineAdapter",
    "MemoryResult",
    "SearchMemoryResponse",
]
