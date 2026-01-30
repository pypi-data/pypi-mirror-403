#!/usr/bin/env python3
"""
Comprehensive test script for Memory Engine Service.

Tests all request scenarios:
1. Ingest with string input
2. Ingest with message list (conversation)
3. Ingest with infer=true/false
4. Search with various parameters
5. Multi-tenant isolation
6. Auth and scope validation
7. Idempotency
8. Error handling

Usage:
    # Start server first:
    export MEMORY_ENGINE_CONFIG=config.test.yaml
    uvicorn memory_engine.main:app --port 8000

    # Run tests:
    python tests/test_comprehensive.py
"""

import asyncio
import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx

BASE_URL = "http://127.0.0.1:8000"


@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class MemoryEngineTestSuite:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results: List[TestResult] = []

    async def run_all(self):
        """Run all test scenarios."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Health check
            await self.test_health(client)

            # Ingest tests - new simplified API
            await self.test_ingest_string_input(client)
            await self.test_ingest_single_message(client)
            await self.test_ingest_message_list(client)
            await self.test_ingest_with_infer_true(client)
            await self.test_ingest_with_infer_false(client)
            await self.test_ingest_with_metadata(client)

            # Search tests
            await self.test_search_basic(client)
            await self.test_search_with_top_k(client)
            await self.test_search_with_filters(client)

            # Multi-tenant isolation
            await self.test_multi_tenant_isolation(client)
            await self.test_cross_tenant_blocked(client)

            # Auth tests
            await self.test_missing_token(client)
            await self.test_invalid_token(client)
            await self.test_scope_mismatch(client)

            # Idempotency tests
            await self.test_idempotency(client)

            # Validation tests
            await self.test_invalid_scope(client)

        self.print_summary()

    def record(self, name: str, passed: bool, message: str, details: Dict = None):
        self.results.append(TestResult(name, passed, message, details))
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            print(f"       {message}")

    async def test_health(self, client: httpx.AsyncClient):
        """Test health endpoint."""
        try:
            resp = await client.get(f"{self.base_url}/health")
            passed = resp.status_code == 200 and resp.json().get("status") == "ok"
            self.record("Health Check", passed, f"Status: {resp.status_code}")
        except Exception as e:
            self.record("Health Check", False, str(e))

    async def test_ingest_string_input(self, client: httpx.AsyncClient):
        """Test ingest with simple string input (Mem0 compatible)."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:ingest",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "test-string"},
                    "messages": "I love playing basketball on weekends.",
                    "metadata": {"test": "string_input"},
                },
            )
            passed = resp.status_code == 200 and len(resp.json().get("items", [])) == 1
            self.record("Ingest (string input)", passed, f"Status: {resp.status_code}", resp.json())
        except Exception as e:
            self.record("Ingest (string input)", False, str(e))

    async def test_ingest_single_message(self, client: httpx.AsyncClient):
        """Test ingest with single message dict."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:ingest",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "test-single"},
                    "messages": {"role": "user", "content": "My favorite color is blue."},
                },
            )
            passed = resp.status_code == 200 and len(resp.json().get("items", [])) == 1
            self.record("Ingest (single message)", passed, f"Status: {resp.status_code}", resp.json())
        except Exception as e:
            self.record("Ingest (single message)", False, str(e))

    async def test_ingest_message_list(self, client: httpx.AsyncClient):
        """Test ingest with message list (conversation)."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:ingest",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "test-conversation"},
                    "messages": [
                        {"role": "user", "content": "I just moved to San Francisco."},
                        {"role": "assistant", "content": "Welcome to SF! How do you like it?"},
                        {"role": "user", "content": "I love hiking in the Bay Area."},
                    ],
                },
            )
            items = resp.json().get("items", [])
            passed = resp.status_code == 200 and len(items) == 3
            self.record("Ingest (message list)", passed, f"Status: {resp.status_code}, Items: {len(items)}")
        except Exception as e:
            self.record("Ingest (message list)", False, str(e))

    async def test_ingest_with_infer_true(self, client: httpx.AsyncClient):
        """Test ingest with infer=true (let Mem0 extract memories)."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:ingest",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "test-infer-true"},
                    "messages": [
                        {"role": "user", "content": "I'm a software engineer at Google and I love Python."},
                    ],
                    "infer": True,
                },
            )
            passed = resp.status_code == 200
            self.record("Ingest (infer=true)", passed, f"Status: {resp.status_code}", resp.json())
        except Exception as e:
            self.record("Ingest (infer=true)", False, str(e))

    async def test_ingest_with_infer_false(self, client: httpx.AsyncClient):
        """Test ingest with infer=false (raw storage)."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:ingest",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "test-infer-false"},
                    "messages": "Direct storage without AI processing.",
                    "infer": False,
                    "metadata": {"type": "fact"},
                },
            )
            items = resp.json().get("items", [])
            passed = resp.status_code == 200 and len(items) == 1
            # Verify content is stored as-is
            if items:
                passed = passed and items[0].get("content") == "Direct storage without AI processing."
            self.record("Ingest (infer=false)", passed, f"Status: {resp.status_code}")
        except Exception as e:
            self.record("Ingest (infer=false)", False, str(e))

    async def test_ingest_with_metadata(self, client: httpx.AsyncClient):
        """Test ingest with rich metadata."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:ingest",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "test-meta"},
                    "messages": "Test with metadata",
                    "metadata": {"lang": "en", "category": "test", "priority": 1},
                },
            )
            passed = resp.status_code == 200
            self.record("Ingest with Metadata", passed, f"Status: {resp.status_code}")
        except Exception as e:
            self.record("Ingest with Metadata", False, str(e))

    async def test_search_basic(self, client: httpx.AsyncClient):
        """Test basic search."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:search",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "user-1"},
                    "query": "hobby",
                    "top_k": 5,
                },
            )
            passed = resp.status_code == 200 and "items" in resp.json()
            self.record("Search Basic", passed, f"Status: {resp.status_code}, Items: {len(resp.json().get('items', []))}")
        except Exception as e:
            self.record("Search Basic", False, str(e))

    async def test_search_with_top_k(self, client: httpx.AsyncClient):
        """Test search with different top_k values."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:search",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "user-1"},
                    "query": "test",
                    "top_k": 1,
                },
            )
            items = resp.json().get("items", [])
            passed = resp.status_code == 200 and len(items) <= 1
            self.record("Search top_k=1", passed, f"Status: {resp.status_code}, Items: {len(items)}")
        except Exception as e:
            self.record("Search top_k=1", False, str(e))

    async def test_search_with_filters(self, client: httpx.AsyncClient):
        """Test search with metadata filters."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:search",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "user-1"},
                    "query": "test",
                    "top_k": 5,
                    "filters": {"category": "test"},
                },
            )
            passed = resp.status_code == 200
            self.record("Search with Filters", passed, f"Status: {resp.status_code}")
        except Exception as e:
            self.record("Search with Filters", False, str(e))

    async def test_multi_tenant_isolation(self, client: httpx.AsyncClient):
        """Test that different tenants have isolated memories."""
        try:
            # Search tenant-a
            resp_a = await client.post(
                f"{self.base_url}/v1/memories:search",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "user-1"},
                    "query": "hobby",
                    "top_k": 10,
                },
            )
            items_a = resp_a.json().get("items", [])

            # Search tenant-b
            resp_b = await client.post(
                f"{self.base_url}/v1/memories:search",
                headers={"Authorization": "Bearer token-tenant-b", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-b", "app_id": "app-1", "user_id": "user-1"},
                    "query": "hobby",
                    "top_k": 10,
                },
            )
            items_b = resp_b.json().get("items", [])

            # Check no overlap in memory_ids
            ids_a = {item["memory_id"] for item in items_a}
            ids_b = {item["memory_id"] for item in items_b}
            no_overlap = len(ids_a & ids_b) == 0

            passed = resp_a.status_code == 200 and resp_b.status_code == 200 and no_overlap
            self.record(
                "Multi-tenant Isolation",
                passed,
                f"Tenant-A: {len(items_a)} items, Tenant-B: {len(items_b)} items, Overlap: {len(ids_a & ids_b)}",
            )
        except Exception as e:
            self.record("Multi-tenant Isolation", False, str(e))

    async def test_cross_tenant_blocked(self, client: httpx.AsyncClient):
        """Test that cross-tenant access is blocked."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:search",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-b", "app_id": "app-1", "user_id": "user-1"},  # Wrong tenant
                    "query": "test",
                    "top_k": 5,
                },
            )
            passed = resp.status_code == 403
            self.record("Cross-tenant Blocked", passed, f"Status: {resp.status_code} (expected 403)")
        except Exception as e:
            self.record("Cross-tenant Blocked", False, str(e))

    async def test_missing_token(self, client: httpx.AsyncClient):
        """Test request without auth token."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:search",
                headers={"Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "user-1"},
                    "query": "test",
                },
            )
            passed = resp.status_code == 401
            self.record("Missing Token", passed, f"Status: {resp.status_code} (expected 401)")
        except Exception as e:
            self.record("Missing Token", False, str(e))

    async def test_invalid_token(self, client: httpx.AsyncClient):
        """Test request with invalid token."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:search",
                headers={"Authorization": "Bearer invalid-token", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "user-1"},
                    "query": "test",
                },
            )
            passed = resp.status_code == 401
            self.record("Invalid Token", passed, f"Status: {resp.status_code} (expected 401)")
        except Exception as e:
            self.record("Invalid Token", False, str(e))

    async def test_scope_mismatch(self, client: httpx.AsyncClient):
        """Test request with mismatched app_id."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:search",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a", "app_id": "wrong-app", "user_id": "user-1"},
                    "query": "test",
                },
            )
            passed = resp.status_code == 403
            self.record("Scope Mismatch (app)", passed, f"Status: {resp.status_code} (expected 403)")
        except Exception as e:
            self.record("Scope Mismatch (app)", False, str(e))

    async def test_idempotency(self, client: httpx.AsyncClient):
        """Test idempotency key for ingest."""
        try:
            idem_key = str(uuid4())
            payload = {
                "scope": {"tenant_id": "tenant-a", "app_id": "app-1", "user_id": "test-idem"},
                "messages": "Idempotency test memory",
            }

            # First request
            resp1 = await client.post(
                f"{self.base_url}/v1/memories:ingest",
                headers={
                    "Authorization": "Bearer token-tenant-a",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idem_key,
                },
                json=payload,
            )

            # Second request with same key
            resp2 = await client.post(
                f"{self.base_url}/v1/memories:ingest",
                headers={
                    "Authorization": "Bearer token-tenant-a",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idem_key,
                },
                json=payload,
            )

            replay_header = resp2.headers.get("X-Idempotent-Replay", "").lower()
            passed = resp1.status_code == 200 and resp2.status_code == 200 and replay_header == "true"
            self.record("Idempotency", passed, f"First: {resp1.status_code}, Second: {resp2.status_code}, Replay: {replay_header}")
        except Exception as e:
            self.record("Idempotency", False, str(e))

    async def test_invalid_scope(self, client: httpx.AsyncClient):
        """Test request with missing required scope fields."""
        try:
            resp = await client.post(
                f"{self.base_url}/v1/memories:search",
                headers={"Authorization": "Bearer token-tenant-a", "Content-Type": "application/json"},
                json={
                    "scope": {"tenant_id": "tenant-a"},  # Missing app_id, user_id
                    "query": "test",
                },
            )
            passed = resp.status_code == 422
            self.record("Invalid Scope", passed, f"Status: {resp.status_code} (expected 422)")
        except Exception as e:
            self.record("Invalid Scope", False, str(e))

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"Total: {total}")
        print(f"Passed: {passed} ({100*passed/total:.1f}%)")
        print(f"Failed: {failed}")

        if failed > 0:
            print("\nFailed tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.message}")

        print("=" * 60)
        return failed == 0


async def main():
    print("=" * 60)
    print("Memory Engine Comprehensive Test Suite")
    print("=" * 60)
    print(f"Target: {BASE_URL}\n")

    suite = MemoryEngineTestSuite()
    await suite.run_all()

    sys.exit(0 if all(r.passed for r in suite.results) else 1)


if __name__ == "__main__":
    asyncio.run(main())
