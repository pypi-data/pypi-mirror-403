"""
ADK BaseMemoryService Adapter for Memory Engine

This module implements Google ADK's BaseMemoryService interface,
enabling ADK agents to use Memory Engine as their long-term memory backend.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

from .client import (
    MemoryEngineClient,
    Scope,
    Message,
    MemoryItem,
)

logger = logging.getLogger(__name__)


# ADK interface types (for type hints when google-adk is not installed)
# These match the ADK interface signatures

@dataclass
class MemoryResult:
    """
    ADK-compatible memory result.

    In ADK, MemoryResult contains a list of events. Since Memory Engine
    stores processed memories rather than raw events, we wrap memory
    content in a simplified event-like structure.
    """
    events: List[Dict[str, Any]]

    # Additional Memory Engine metadata
    memory_id: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class SearchMemoryResponse:
    """ADK-compatible search response."""
    memories: List[MemoryResult]


class BaseMemoryService(ABC):
    """
    Abstract base class matching ADK's BaseMemoryService interface.

    This is provided for standalone usage. When using with actual ADK,
    inherit from google.adk.memory.BaseMemoryService instead.
    """

    @abstractmethod
    async def add_session_to_memory(self, session: Any) -> None:
        """Add session content to memory storage."""
        pass

    @abstractmethod
    async def search_memory(
        self,
        *,
        app_name: str,
        user_id: str,
        query: str,
    ) -> SearchMemoryResponse:
        """Search for relevant memories."""
        pass


class MemoryEngineAdapter(BaseMemoryService):
    """
    ADK MemoryService adapter that uses Memory Engine as backend.

    This adapter implements ADK's BaseMemoryService interface, translating
    ADK session events and search queries into Memory Engine API calls.

    Example:
        from memory_engine_adapters.adk_adapter import MemoryEngineAdapter

        # Create adapter
        adapter = MemoryEngineAdapter(
            base_url="http://localhost:8000",
            token="your-bearer-token",
            tenant_id="your-tenant"
        )

        # Use with ADK Runner
        from google.adk.runners import Runner
        runner = Runner(
            agent=your_agent,
            app_name="my-app",
            session_service=session_service,
            memory_service=adapter
        )

    Memory Engine Scope Mapping:
        - tenant_id: Configured at adapter initialization
        - app_id: From ADK's app_name
        - user_id: From ADK's user_id
        - agent_id: Extracted from session if available
        - session_id: Extracted from session if available
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: str = "demo-token",
        tenant_id: str = "demo-tenant",
        ingest_mode: str = "infer",
        timeout: float = 30.0,
    ):
        """
        Initialize the adapter.

        Args:
            base_url: Memory Engine API base URL
            token: Bearer token for authentication
            tenant_id: Tenant ID for multi-tenant isolation
            ingest_mode: Default ingest mode ("raw" or "infer")
                - "raw": Store memories as-is (infer=False)
                - "infer": Let Memory Engine extract memories from content (infer=True)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.token = token
        self.tenant_id = tenant_id
        self.ingest_mode = ingest_mode
        self.timeout = timeout

        self._client: Optional[MemoryEngineClient] = None

    def _get_client(self) -> MemoryEngineClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = MemoryEngineClient(
                base_url=self.base_url,
                token=self.token,
                timeout=self.timeout,
            )
        return self._client

    def _build_scope(
        self,
        app_name: str,
        user_id: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Scope:
        """Build Memory Engine scope from ADK context."""
        return Scope(
            tenant_id=self.tenant_id,
            app_id=app_name,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            run_id=run_id,
        )

    def _extract_session_info(self, session: Any) -> Dict[str, Any]:
        """
        Extract relevant information from ADK Session.

        ADK Session typically has:
        - app_name: str
        - user_id: str
        - events: List[Event] - conversation history
        - state: Dict - session state
        """
        info = {
            "app_name": getattr(session, "app_name", "unknown"),
            "user_id": getattr(session, "user_id", "unknown"),
            "agent_id": getattr(session, "agent_id", None),
            "session_id": getattr(session, "id", None) or getattr(session, "session_id", None),
            "events": getattr(session, "events", []),
            "state": getattr(session, "state", {}),
        }
        return info

    def _events_to_messages(
        self,
        events: List[Any],
        session_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Convert ADK events to Memory Engine message format.

        Returns a list of message dicts: [{"role": "user", "content": "..."}]
        """
        messages = []
        for event in events:
            content = self._extract_event_content(event)
            if content:
                role = self._extract_event_role(event)
                messages.append({"role": role, "content": content})
        return messages

    def _extract_event_content(self, event: Any) -> Optional[str]:
        """Extract text content from an ADK event."""
        # Try common ADK event attributes
        if hasattr(event, "content"):
            content = event.content
            if isinstance(content, str):
                return content
            if hasattr(content, "text"):
                return content.text
            if isinstance(content, dict) and "text" in content:
                return content["text"]

        if hasattr(event, "text"):
            return event.text

        if hasattr(event, "message"):
            msg = event.message
            if isinstance(msg, str):
                return msg
            if hasattr(msg, "content"):
                return msg.content

        # Handle dict-like events
        if isinstance(event, dict):
            return event.get("content") or event.get("text") or event.get("message")

        return None

    def _extract_event_role(self, event: Any) -> str:
        """Extract role (user/assistant/system) from an ADK event."""
        if hasattr(event, "role"):
            return str(event.role)
        if hasattr(event, "author"):
            return str(event.author)
        if isinstance(event, dict):
            return event.get("role", "user") or event.get("author", "user")
        return "user"

    def _memory_item_to_result(self, item: MemoryItem) -> MemoryResult:
        """Convert Memory Engine MemoryItem to ADK MemoryResult."""
        # Create event-like structure for ADK compatibility
        event = {
            "content": item.content,
            "metadata": item.metadata,
        }

        return MemoryResult(
            events=[event],
            memory_id=item.memory_id,
            created_at=item.created_at.isoformat() if item.created_at else None,
        )

    async def add_session_to_memory(self, session: Any) -> None:
        """
        Add session content to Memory Engine.

        This method extracts conversation events from the ADK session
        and ingests them into Memory Engine for long-term storage.

        Args:
            session: ADK Session object containing:
                - app_name: Application identifier
                - user_id: User identifier
                - events: List of conversation events
                - state: Optional session state
        """
        session_info = self._extract_session_info(session)

        if not session_info["events"]:
            logger.debug("No events in session, skipping memory ingestion")
            return

        scope = self._build_scope(
            app_name=session_info["app_name"],
            user_id=session_info["user_id"],
            agent_id=session_info["agent_id"],
            session_id=session_info["session_id"],
        )

        messages = self._events_to_messages(
            events=session_info["events"],
            session_id=session_info["session_id"],
        )

        if not messages:
            logger.debug("No messages extracted from session events")
            return

        client = self._get_client()
        try:
            # Use the new simplified API
            # ingest_mode "infer" -> infer=True, "raw" -> infer=False
            items = await client.ingest(
                scope=scope,
                messages=messages,
                infer=(self.ingest_mode == "infer"),
                metadata={"source": "adk_session", "session_id": session_info["session_id"]},
            )
            logger.info(
                f"Ingested {len(items)} memories for user={session_info['user_id']}, "
                f"app={session_info['app_name']}"
            )
        except Exception as e:
            logger.error(f"Failed to ingest session memories: {e}")
            raise

    async def search_memory(
        self,
        *,
        app_name: str,
        user_id: str,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> SearchMemoryResponse:
        """
        Search for relevant memories in Memory Engine.

        Args:
            app_name: Application identifier (maps to Memory Engine app_id)
            user_id: User identifier
            query: Natural language search query
            top_k: Maximum number of results (default: 5)
            threshold: Minimum similarity threshold (default: 0.0)

        Returns:
            SearchMemoryResponse containing matching memories as MemoryResult objects
        """
        scope = self._build_scope(
            app_name=app_name,
            user_id=user_id,
        )

        client = self._get_client()
        try:
            items = await client.search(
                scope=scope,
                query=query,
                top_k=top_k,
                threshold=threshold,
            )

            memories = [self._memory_item_to_result(item) for item in items]
            logger.debug(
                f"Found {len(memories)} memories for query='{query}', "
                f"user={user_id}, app={app_name}"
            )
            return SearchMemoryResponse(memories=memories)

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            raise

    async def close(self) -> None:
        """Close the adapter and release resources."""
        if self._client:
            await self._client.close()
            self._client = None
