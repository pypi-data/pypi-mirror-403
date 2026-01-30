"""
Tests for ADK Memory Adapter

Run with: pytest tests/test_adk_adapter.py -v
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import List

from memory_engine_adapters.adk_adapter.client import (
    MemoryEngineClient,
    Scope,
    Message,
    MemoryItem,
    MemoryEngineError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
)
from memory_engine_adapters.adk_adapter.adapter import (
    MemoryEngineAdapter,
    MemoryResult,
    SearchMemoryResponse,
)


# Test data fixtures

@dataclass
class MockEvent:
    """Mock ADK event."""
    role: str
    content: str


@dataclass
class MockSession:
    """Mock ADK session."""
    app_name: str
    user_id: str
    session_id: str
    events: List[MockEvent]
    state: dict


@pytest.fixture
def sample_scope():
    return Scope(
        tenant_id="test-tenant",
        app_id="test-app",
        user_id="test-user",
        agent_id="agent-1",
        session_id="session-1",
    )


@pytest.fixture
def sample_memory_item(sample_scope):
    return MemoryItem(
        memory_id="mem-123",
        scope=sample_scope,
        content="User likes coffee",
        metadata={"lang": "en"},
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_session():
    return MockSession(
        app_name="test-app",
        user_id="test-user",
        session_id="session-001",
        events=[
            MockEvent(role="user", content="Hello, my name is Alice."),
            MockEvent(role="assistant", content="Nice to meet you, Alice!"),
            MockEvent(role="user", content="I love Python programming."),
        ],
        state={"mood": "friendly"},
    )


# Client tests

class TestScope:
    def test_to_dict_required_fields(self):
        scope = Scope(
            tenant_id="t1",
            app_id="a1",
            user_id="u1",
        )
        d = scope.to_dict()
        assert d == {
            "tenant_id": "t1",
            "app_id": "a1",
            "user_id": "u1",
        }

    def test_to_dict_all_fields(self, sample_scope):
        d = sample_scope.to_dict()
        assert d["tenant_id"] == "test-tenant"
        assert d["app_id"] == "test-app"
        assert d["user_id"] == "test-user"
        assert d["agent_id"] == "agent-1"
        assert d["session_id"] == "session-1"


class TestMessage:
    def test_to_dict(self):
        msg = Message(role="user", content="Hello")
        assert msg.to_dict() == {"role": "user", "content": "Hello"}

    def test_default_role(self):
        msg = Message(content="Hello")
        assert msg.role == "user"


class TestMemoryItem:
    def test_from_dict(self):
        data = {
            "memory_id": "mem-456",
            "scope": {
                "tenant_id": "t1",
                "app_id": "a1",
                "user_id": "u1",
            },
            "content": "Test content",
            "metadata": {"key": "value"},
            "created_at": "2024-01-15T10:30:00+00:00",
        }
        item = MemoryItem.from_dict(data)
        assert item.memory_id == "mem-456"
        assert item.scope.tenant_id == "t1"
        assert item.content == "Test content"
        assert item.metadata == {"key": "value"}


class TestMemoryEngineClient:
    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with MemoryEngineClient(
            base_url="http://localhost:8000",
            token="test-token",
        ) as client:
            assert client._client is not None

    @pytest.mark.asyncio
    async def test_ingest_string_input(self, sample_scope, sample_memory_item):
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [{
                    "memory_id": "mem-123",
                    "scope": sample_scope.to_dict(),
                    "content": "User likes coffee",
                    "metadata": {},
                    "created_at": "2024-01-15T10:30:00+00:00",
                }]
            }

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            client = MemoryEngineClient(
                base_url="http://localhost:8000",
                token="test-token",
            )
            client._client = mock_client

            # Test string input
            items = await client.ingest(
                scope=sample_scope,
                messages="User likes coffee",
            )

            assert len(items) == 1
            assert items[0].memory_id == "mem-123"

    @pytest.mark.asyncio
    async def test_ingest_message_list(self, sample_scope, sample_memory_item):
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [{
                    "memory_id": "mem-123",
                    "scope": sample_scope.to_dict(),
                    "content": "User likes coffee",
                    "metadata": {},
                    "created_at": "2024-01-15T10:30:00+00:00",
                }]
            }

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            client = MemoryEngineClient(
                base_url="http://localhost:8000",
                token="test-token",
            )
            client._client = mock_client

            # Test message list input
            items = await client.ingest(
                scope=sample_scope,
                messages=[
                    {"role": "user", "content": "I love coffee"},
                    {"role": "assistant", "content": "That's great!"},
                ],
            )

            assert len(items) == 1
            assert items[0].memory_id == "mem-123"

    @pytest.mark.asyncio
    async def test_search_success(self, sample_scope):
        with patch("httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [{
                    "memory_id": "mem-123",
                    "scope": sample_scope.to_dict(),
                    "content": "User likes coffee",
                    "metadata": {},
                    "created_at": "2024-01-15T10:30:00+00:00",
                }]
            }

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            client = MemoryEngineClient(
                base_url="http://localhost:8000",
                token="test-token",
            )
            client._client = mock_client

            items = await client.search(
                scope=sample_scope,
                query="what does user like",
            )

            assert len(items) == 1
            assert items[0].content == "User likes coffee"

    @pytest.mark.asyncio
    async def test_error_handling_auth(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "code": "AUTH_INVALID_TOKEN",
            "message": "Invalid token",
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        client = MemoryEngineClient(
            base_url="http://localhost:8000",
            token="invalid-token",
        )
        client._client = mock_client

        with pytest.raises(AuthenticationError) as exc_info:
            await client.search(
                scope=Scope(tenant_id="t", app_id="a", user_id="u"),
                query="test",
            )

        assert exc_info.value.code == "AUTH_INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_error_handling_rate_limit(self):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "code": "RATE_LIMITED",
            "message": "Rate limit exceeded",
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        client = MemoryEngineClient(
            base_url="http://localhost:8000",
            token="test-token",
        )
        client._client = mock_client

        with pytest.raises(RateLimitError):
            await client.search(
                scope=Scope(tenant_id="t", app_id="a", user_id="u"),
                query="test",
            )


# Adapter tests

class TestMemoryEngineAdapter:
    def test_init_defaults(self):
        adapter = MemoryEngineAdapter()
        assert adapter.base_url == "http://localhost:8000"
        assert adapter.token == "demo-token"
        assert adapter.tenant_id == "demo-tenant"
        assert adapter.ingest_mode == "infer"

    def test_init_custom(self):
        adapter = MemoryEngineAdapter(
            base_url="http://custom:9000",
            token="custom-token",
            tenant_id="custom-tenant",
            ingest_mode="raw",
        )
        assert adapter.base_url == "http://custom:9000"
        assert adapter.token == "custom-token"
        assert adapter.tenant_id == "custom-tenant"
        assert adapter.ingest_mode == "raw"

    def test_build_scope(self):
        adapter = MemoryEngineAdapter(tenant_id="my-tenant")
        scope = adapter._build_scope(
            app_name="my-app",
            user_id="user-123",
            agent_id="agent-1",
        )
        assert scope.tenant_id == "my-tenant"
        assert scope.app_id == "my-app"
        assert scope.user_id == "user-123"
        assert scope.agent_id == "agent-1"

    def test_extract_session_info(self, sample_session):
        adapter = MemoryEngineAdapter()
        info = adapter._extract_session_info(sample_session)

        assert info["app_name"] == "test-app"
        assert info["user_id"] == "test-user"
        assert info["session_id"] == "session-001"
        assert len(info["events"]) == 3

    def test_events_to_messages(self, sample_session):
        adapter = MemoryEngineAdapter()
        messages = adapter._events_to_messages(
            events=sample_session.events,
            session_id="session-001",
        )

        assert len(messages) == 3
        assert messages[0] == {"role": "user", "content": "Hello, my name is Alice."}
        assert messages[1] == {"role": "assistant", "content": "Nice to meet you, Alice!"}
        assert messages[2] == {"role": "user", "content": "I love Python programming."}

    def test_extract_event_content_attr(self):
        adapter = MemoryEngineAdapter()

        event = MockEvent(role="user", content="Test content")
        content = adapter._extract_event_content(event)
        assert content == "Test content"

    def test_extract_event_content_dict(self):
        adapter = MemoryEngineAdapter()

        event = {"content": "Dict content", "role": "user"}
        content = adapter._extract_event_content(event)
        assert content == "Dict content"

    def test_extract_event_role(self):
        adapter = MemoryEngineAdapter()

        event = MockEvent(role="assistant", content="Hi")
        role = adapter._extract_event_role(event)
        assert role == "assistant"

    def test_memory_item_to_result(self, sample_memory_item):
        adapter = MemoryEngineAdapter()
        result = adapter._memory_item_to_result(sample_memory_item)

        assert isinstance(result, MemoryResult)
        assert len(result.events) == 1
        assert result.events[0]["content"] == "User likes coffee"
        assert result.memory_id == "mem-123"

    @pytest.mark.asyncio
    async def test_add_session_to_memory(self, sample_session, sample_memory_item):
        adapter = MemoryEngineAdapter()

        mock_client = AsyncMock()
        mock_client.ingest = AsyncMock(return_value=[sample_memory_item])
        adapter._client = mock_client

        await adapter.add_session_to_memory(sample_session)

        mock_client.ingest.assert_called_once()
        call_args = mock_client.ingest.call_args
        assert call_args.kwargs["scope"].app_id == "test-app"
        assert call_args.kwargs["scope"].user_id == "test-user"
        # Check that messages are passed (new API)
        assert "messages" in call_args.kwargs
        assert len(call_args.kwargs["messages"]) == 3

    @pytest.mark.asyncio
    async def test_add_session_empty_events(self):
        adapter = MemoryEngineAdapter()

        session = MockSession(
            app_name="test-app",
            user_id="test-user",
            session_id="session-001",
            events=[],
            state={},
        )

        mock_client = AsyncMock()
        adapter._client = mock_client

        await adapter.add_session_to_memory(session)

        # Should not call ingest when no events
        mock_client.ingest.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_memory(self, sample_memory_item):
        adapter = MemoryEngineAdapter()

        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value=[sample_memory_item])
        adapter._client = mock_client

        response = await adapter.search_memory(
            app_name="test-app",
            user_id="test-user",
            query="what does user like",
        )

        assert isinstance(response, SearchMemoryResponse)
        assert len(response.memories) == 1
        assert response.memories[0].events[0]["content"] == "User likes coffee"

        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args
        assert call_args.kwargs["scope"].app_id == "test-app"
        assert call_args.kwargs["query"] == "what does user like"

    @pytest.mark.asyncio
    async def test_search_memory_with_params(self, sample_memory_item):
        adapter = MemoryEngineAdapter()

        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value=[sample_memory_item])
        adapter._client = mock_client

        await adapter.search_memory(
            app_name="test-app",
            user_id="test-user",
            query="test query",
            top_k=10,
            threshold=0.5,
        )

        call_args = mock_client.search.call_args
        assert call_args.kwargs["top_k"] == 10
        assert call_args.kwargs["threshold"] == 0.5

    @pytest.mark.asyncio
    async def test_ingest_mode_infer(self, sample_session, sample_memory_item):
        """Test that ingest_mode='infer' sets infer=True"""
        adapter = MemoryEngineAdapter(ingest_mode="infer")

        mock_client = AsyncMock()
        mock_client.ingest = AsyncMock(return_value=[sample_memory_item])
        adapter._client = mock_client

        await adapter.add_session_to_memory(sample_session)

        call_args = mock_client.ingest.call_args
        assert call_args.kwargs["infer"] is True

    @pytest.mark.asyncio
    async def test_ingest_mode_raw(self, sample_session, sample_memory_item):
        """Test that ingest_mode='raw' sets infer=False"""
        adapter = MemoryEngineAdapter(ingest_mode="raw")

        mock_client = AsyncMock()
        mock_client.ingest = AsyncMock(return_value=[sample_memory_item])
        adapter._client = mock_client

        await adapter.add_session_to_memory(sample_session)

        call_args = mock_client.ingest.call_args
        assert call_args.kwargs["infer"] is False


# Integration-like tests (require running server)

class TestIntegration:
    """
    Integration tests that require a running Memory Engine server.
    Skip these in CI unless server is available.
    """

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires running Memory Engine server")
    async def test_full_flow(self):
        adapter = MemoryEngineAdapter(
            base_url="http://localhost:8000",
            token="demo-token",
            tenant_id="demo-tenant",
        )

        session = MockSession(
            app_name="demo-app",
            user_id="integration-test-user",
            session_id="session-integration",
            events=[
                MockEvent(role="user", content="I love hiking in the mountains."),
                MockEvent(role="assistant", content="That sounds wonderful!"),
            ],
            state={},
        )

        # Ingest
        await adapter.add_session_to_memory(session)

        # Search
        response = await adapter.search_memory(
            app_name="demo-app",
            user_id="integration-test-user",
            query="what activities does user enjoy",
        )

        assert response.memories is not None

        await adapter.close()
