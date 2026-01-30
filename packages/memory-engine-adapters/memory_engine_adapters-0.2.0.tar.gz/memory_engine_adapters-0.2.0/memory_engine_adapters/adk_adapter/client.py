"""
Memory Engine HTTP Client

Provides async HTTP client for interacting with Memory Engine API.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

import httpx


@dataclass
class Scope:
    """Memory scope for isolation."""
    tenant_id: str
    app_id: str
    user_id: str
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    run_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "tenant_id": self.tenant_id,
            "app_id": self.app_id,
            "user_id": self.user_id,
        }
        if self.agent_id:
            d["agent_id"] = self.agent_id
        if self.session_id:
            d["session_id"] = self.session_id
        if self.run_id:
            d["run_id"] = self.run_id
        return d


@dataclass
class Message:
    """Message for ingest (aligns with Mem0 format)."""
    role: Literal["user", "assistant", "system"] = "user"
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "content": self.content}


@dataclass
class MemoryItem:
    """Complete memory item returned from API."""
    memory_id: str
    scope: Scope
    content: str
    metadata: Dict[str, Any]
    created_at: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        scope_data = data["scope"]
        scope = Scope(
            tenant_id=scope_data["tenant_id"],
            app_id=scope_data["app_id"],
            user_id=scope_data["user_id"],
            agent_id=scope_data.get("agent_id"),
            session_id=scope_data.get("session_id"),
            run_id=scope_data.get("run_id"),
        )

        created_at = data["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return cls(
            memory_id=data["memory_id"],
            scope=scope,
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            created_at=created_at,
        )


class MemoryEngineError(Exception):
    """Base exception for Memory Engine errors."""

    def __init__(self, code: str, message: str, status_code: int, details: Optional[Dict] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(f"{code}: {message}")


class AuthenticationError(MemoryEngineError):
    """Authentication failed."""
    pass


class AuthorizationError(MemoryEngineError):
    """Authorization failed (scope forbidden)."""
    pass


class RateLimitError(MemoryEngineError):
    """Rate limit exceeded."""
    pass


class ValidationError(MemoryEngineError):
    """Validation error."""
    pass


class ProviderUnavailableError(MemoryEngineError):
    """Provider unavailable."""
    pass


# Type alias for messages input (matches Mem0's flexible input)
MessagesInput = Union[str, Message, Dict[str, str], List[Union[Message, Dict[str, str]]]]


class MemoryEngineClient:
    """
    Async HTTP client for Memory Engine API.

    Example:
        async with MemoryEngineClient(
            base_url="http://localhost:8000",
            token="demo-token"
        ) as client:
            # Ingest memories (string input - simplest)
            items = await client.ingest(
                scope=Scope(tenant_id="demo-tenant", app_id="demo-app", user_id="user-1"),
                messages="User likes coffee"
            )

            # Ingest memories (conversation)
            items = await client.ingest(
                scope=Scope(tenant_id="demo-tenant", app_id="demo-app", user_id="user-1"),
                messages=[
                    {"role": "user", "content": "I love coffee"},
                    {"role": "assistant", "content": "That's great!"}
                ]
            )

            # Search memories
            results = await client.search(
                scope=Scope(tenant_id="demo-tenant", app_id="demo-app", user_id="user-1"),
                query="what does user like"
            )
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: str = "demo-token",
        timeout: float = 30.0,
    ):
        """
        Initialize the client.

        Args:
            base_url: Memory Engine API base URL
            token: Bearer token for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "MemoryEngineClient":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Authorization": f"Bearer {self.token}"},
            )
        return self._client

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error response and raise appropriate exception."""
        try:
            data = response.json()
            code = data.get("code", "UNKNOWN_ERROR")
            message = data.get("message", "Unknown error")
            details = data.get("details", {})
        except Exception:
            code = "UNKNOWN_ERROR"
            message = response.text or "Unknown error"
            details = {}

        error_classes = {
            "AUTH_MISSING_TOKEN": AuthenticationError,
            "AUTH_INVALID_TOKEN": AuthenticationError,
            "SCOPE_FORBIDDEN": AuthorizationError,
            "RATE_LIMITED": RateLimitError,
            "VALIDATION_ERROR": ValidationError,
            "PROVIDER_UNAVAILABLE": ProviderUnavailableError,
        }

        error_class = error_classes.get(code, MemoryEngineError)
        raise error_class(code, message, response.status_code, details)

    def _normalize_messages(self, messages: MessagesInput) -> Any:
        """
        Normalize messages input to the format expected by the API.

        The API accepts:
        - string: "I love coffee"
        - single message: {"role": "user", "content": "..."}
        - message list: [{"role": "user", "content": "..."}, ...]
        """
        if isinstance(messages, str):
            return messages
        elif isinstance(messages, Message):
            return messages.to_dict()
        elif isinstance(messages, dict):
            return messages
        elif isinstance(messages, list):
            return [
                m.to_dict() if isinstance(m, Message) else m
                for m in messages
            ]
        else:
            return messages

    async def ingest(
        self,
        scope: Scope,
        messages: MessagesInput,
        metadata: Optional[Dict[str, Any]] = None,
        infer: bool = True,
        idempotency_key: Optional[str] = None,
    ) -> List[MemoryItem]:
        """
        Ingest memories into Memory Engine.

        Args:
            scope: Memory scope (tenant, app, user, etc.)
            messages: Input content - can be:
                - string: "I love coffee"
                - single message: {"role": "user", "content": "..."}
                - message list: [{"role": "user", "content": "..."}, ...]
            metadata: Optional metadata to attach to memories
            infer: If True (default), let Mem0 extract memories from conversation.
                   If False, store messages directly.
            idempotency_key: Optional idempotency key for deduplication

        Returns:
            List of ingested memory items

        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If scope is forbidden
            RateLimitError: If rate limit exceeded
            ValidationError: If request validation fails
            ProviderUnavailableError: If provider is unavailable
        """
        client = self._get_client()

        payload = {
            "scope": scope.to_dict(),
            "messages": self._normalize_messages(messages),
            "metadata": metadata or {},
            "infer": infer,
        }

        headers = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        response = await client.post("/v1/memories:ingest", json=payload, headers=headers)

        if response.status_code != 200:
            self._handle_error(response)

        data = response.json()
        return [MemoryItem.from_dict(item) for item in data.get("items", [])]

    async def search(
        self,
        scope: Scope,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[MemoryItem]:
        """
        Search memories in Memory Engine.

        Args:
            scope: Memory scope (tenant, app, user, etc.)
            query: Search query string
            filters: Optional metadata filters
            top_k: Maximum number of results (1-50)
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of matching memory items

        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If scope is forbidden
            RateLimitError: If rate limit exceeded
            ValidationError: If request validation fails
            ProviderUnavailableError: If provider is unavailable
        """
        client = self._get_client()

        payload = {
            "scope": scope.to_dict(),
            "query": query,
            "filters": filters or {},
            "top_k": top_k,
            "threshold": threshold,
        }

        response = await client.post("/v1/memories:search", json=payload)

        if response.status_code != 200:
            self._handle_error(response)

        data = response.json()
        return [MemoryItem.from_dict(item) for item in data.get("items", [])]

    async def health(self) -> Dict[str, Any]:
        """
        Check Memory Engine health.

        Returns:
            Health status dict
        """
        client = self._get_client()
        response = await client.get("/health")

        if response.status_code != 200:
            self._handle_error(response)

        return response.json()

    async def close(self) -> None:
        """Close the client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Keep old names as aliases for backward compatibility
MemoryContent = Message  # Deprecated alias
IngestMemory = Message   # Deprecated alias
MemorySource = None      # Removed - use metadata instead
