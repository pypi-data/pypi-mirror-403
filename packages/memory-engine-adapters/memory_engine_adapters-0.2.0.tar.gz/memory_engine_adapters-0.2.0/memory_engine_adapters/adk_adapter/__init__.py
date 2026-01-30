"""
ADK MemoryService Adapter for Memory Engine.

Canonical import path (new):
    from memory_engine_adapters.adk_adapter import MemoryEngineAdapter

Backward-compatible (legacy):
    from adk_adapter import MemoryEngineAdapter
"""

from .client import MemoryEngineClient
from .adapter import MemoryEngineAdapter

__all__ = ["MemoryEngineClient", "MemoryEngineAdapter"]
__version__ = "0.2.0"
