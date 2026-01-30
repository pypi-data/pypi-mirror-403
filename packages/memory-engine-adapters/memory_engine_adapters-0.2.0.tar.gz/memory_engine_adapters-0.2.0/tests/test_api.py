import pytest
from fastapi.testclient import TestClient

from memory_engine.config import ProviderConfig, RateLimitConfig, Settings, TokenConfig
from memory_engine.main import create_app


def build_app(rate_limit_per_minute: int = 100) -> TestClient:
    settings = Settings(
        tokens={
            "test-token": TokenConfig(
                tenant_id="t1",
                apps=["app1"],
                rate_limit_per_minute=rate_limit_per_minute,
            )
        },
        rate_limit=RateLimitConfig(default_per_minute=rate_limit_per_minute),
        provider=ProviderConfig(kind="in_memory"),
        audit_enabled=False,
    )
    app = create_app(settings)
    return TestClient(app)


def auth_headers():
    return {"Authorization": "Bearer test-token"}


def base_scope(user_id: str) -> dict:
    return {"tenant_id": "t1", "app_id": "app1", "user_id": user_id}


def test_ingest_string_format():
    """Test ingest with simple string input (Mem0 compatible)."""
    client = build_app()
    ingest_body = {
        "scope": base_scope("u1"),
        "messages": "Paris is the capital of France.",
        "metadata": {"topic": "travel"},
    }
    resp = client.post("/v1/memories:ingest", json=ingest_body, headers=auth_headers())
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["content"] == "Paris is the capital of France."


def test_ingest_single_message_format():
    """Test ingest with single message dict input."""
    client = build_app()
    ingest_body = {
        "scope": base_scope("u1"),
        "messages": {"role": "user", "content": "I love basketball"},
    }
    resp = client.post("/v1/memories:ingest", json=ingest_body, headers=auth_headers())
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["content"] == "I love basketball"


def test_ingest_message_list_format():
    """Test ingest with message list input (conversation)."""
    client = build_app()
    ingest_body = {
        "scope": base_scope("u1"),
        "messages": [
            {"role": "user", "content": "I recently moved to Shanghai"},
            {"role": "assistant", "content": "Welcome to Shanghai!"},
        ],
    }
    resp = client.post("/v1/memories:ingest", json=ingest_body, headers=auth_headers())
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["items"]) == 2


def test_ingest_and_search_success():
    """Test basic ingest and search flow."""
    client = build_app()
    ingest_body = {
        "scope": base_scope("u1"),
        "messages": "Paris is the capital of France.",
        "metadata": {"topic": "travel"},
    }
    resp = client.post("/v1/memories:ingest", json=ingest_body, headers=auth_headers())
    assert resp.status_code == 200, resp.text

    search_body = {
        "scope": base_scope("u1"),
        "query": "capital of France",
        "top_k": 5,
    }
    search_resp = client.post("/v1/memories:search", json=search_body, headers=auth_headers())
    assert search_resp.status_code == 200, search_resp.text
    data = search_resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["content"] == "Paris is the capital of France."


def test_cross_user_isolation():
    """Test that different users cannot see each other's memories."""
    client = build_app()
    ingest_body = {
        "scope": base_scope("u1"),
        "messages": "User one secret.",
    }
    client.post("/v1/memories:ingest", json=ingest_body, headers=auth_headers())

    search_body = {"scope": base_scope("u2"), "query": "secret", "top_k": 5}
    resp = client.post("/v1/memories:search", json=search_body, headers=auth_headers())
    assert resp.status_code == 200, resp.text
    assert resp.json()["items"] == []


def test_rate_limit_enforced():
    """Test that rate limiting works."""
    client = build_app(rate_limit_per_minute=1)
    body = {
        "scope": base_scope("u1"),
        "messages": "hello",
    }
    first = client.post("/v1/memories:ingest", json=body, headers=auth_headers())
    assert first.status_code == 200, first.text

    second = client.post("/v1/memories:ingest", json=body, headers=auth_headers())
    assert second.status_code == 429
    assert second.json()["code"] == "RATE_LIMITED"


def test_ingest_idempotency_key_replay():
    """Test idempotency key prevents duplicate processing."""
    client = build_app()
    body = {
        "scope": base_scope("u1"),
        "messages": "idempotent test",
    }
    headers = {**auth_headers(), "Idempotency-Key": "req-1"}

    first = client.post("/v1/memories:ingest", json=body, headers=headers)
    assert first.status_code == 200, first.text

    second = client.post("/v1/memories:ingest", json=body, headers=headers)
    assert second.status_code == 200
    assert second.headers.get("X-Idempotent-Replay") == "true"
    assert second.json()["items"] == first.json()["items"]


def test_ingest_with_infer_false():
    """Test ingest with infer=false (raw mode)."""
    client = build_app()
    body = {
        "scope": base_scope("u1"),
        "messages": "Direct storage without inference",
        "infer": False,
        "metadata": {"type": "fact"},
    }
    resp = client.post("/v1/memories:ingest", json=body, headers=auth_headers())
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["content"] == "Direct storage without inference"
