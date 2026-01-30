"""
Compatibility shim for legacy imports.

The canonical package is now `memory_engine_adapters.adk_adapter`.
This module simply re-exports the public API to avoid breaking existing code.
"""

from memory_engine_adapters.adk_adapter import MemoryEngineAdapter, MemoryEngineClient

__all__ = ["MemoryEngineAdapter", "MemoryEngineClient"]
