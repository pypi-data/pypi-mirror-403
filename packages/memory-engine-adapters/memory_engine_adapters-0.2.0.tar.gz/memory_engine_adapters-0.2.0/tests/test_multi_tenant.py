#!/usr/bin/env python3
"""
Multi-tenant, multi-user, multi-round test for Memory Engine with Mem0 provider.

Test scenarios:
1. Two tenants (tenant-a, tenant-b)
2. Two users per tenant (user-1, user-2)
3. Multiple rounds of conversation per user
4. Isolation verification: tenant-a users cannot see tenant-b memories
"""

import asyncio
import httpx
import json
import time
from dataclasses import dataclass
from typing import List, Dict, Any

BASE_URL = "http://127.0.0.1:8000"

@dataclass
class TestUser:
    token: str
    tenant_id: str
    app_id: str
    user_id: str
    memories: List[str]  # memories to ingest
    search_queries: List[str]  # queries to search


# Test data setup
TEST_USERS = [
    # Tenant A users
    TestUser(
        token="token-tenant-a",
        tenant_id="tenant-a",
        app_id="app-1",
        user_id="user-1",
        memories=[
            "I love playing tennis on weekends",
            "My favorite food is sushi",
            "I work as a software engineer at Google",
        ],
        search_queries=["what sports do I like", "what is my job"],
    ),
    TestUser(
        token="token-tenant-a",
        tenant_id="tenant-a",
        app_id="app-1",
        user_id="user-2",
        memories=[
            "I enjoy hiking in the mountains",
            "My favorite movie is Inception",
            "I have a pet dog named Max",
        ],
        search_queries=["what are my hobbies", "do I have pets"],
    ),
    # Tenant B users - same user_ids but different tenant
    TestUser(
        token="token-tenant-b",
        tenant_id="tenant-b",
        app_id="app-1",
        user_id="user-1",  # Same user_id as tenant-a/user-1
        memories=[
            "I love swimming in the ocean",
            "My favorite food is pizza",
            "I work as a doctor at a hospital",
        ],
        search_queries=["what sports do I like", "what is my job"],
    ),
    TestUser(
        token="token-tenant-b",
        tenant_id="tenant-b",
        app_id="app-1",
        user_id="user-2",
        memories=[
            "I enjoy reading science fiction books",
            "My favorite movie is The Matrix",
            "I have a pet cat named Luna",
        ],
        search_queries=["what are my hobbies", "do I have pets"],
    ),
]


async def ingest_memory(client: httpx.AsyncClient, user: TestUser, text: str) -> Dict[str, Any]:
    """Ingest a single memory for a user."""
    response = await client.post(
        f"{BASE_URL}/v1/memories:ingest",
        headers={
            "Authorization": f"Bearer {user.token}",
            "Content-Type": "application/json",
        },
        json={
            "scope": {
                "tenant_id": user.tenant_id,
                "app_id": user.app_id,
                "user_id": user.user_id,
            },
            "mode": "raw",
            "memories": [
                {
                    "type": "fact",
                    "content": {"text": text},
                    "metadata": {"round": "test"},
                }
            ],
        },
    )
    response.raise_for_status()
    return response.json()


async def search_memory(client: httpx.AsyncClient, user: TestUser, query: str, top_k: int = 5) -> Dict[str, Any]:
    """Search memories for a user."""
    response = await client.post(
        f"{BASE_URL}/v1/memories:search",
        headers={
            "Authorization": f"Bearer {user.token}",
            "Content-Type": "application/json",
        },
        json={
            "scope": {
                "tenant_id": user.tenant_id,
                "app_id": user.app_id,
                "user_id": user.user_id,
            },
            "query": query,
            "top_k": top_k,
        },
    )
    response.raise_for_status()
    return response.json()


async def run_user_test(client: httpx.AsyncClient, user: TestUser) -> None:
    """Run multi-round test for a single user."""
    print(f"\n{'='*60}")
    print(f"Testing: {user.tenant_id}/{user.user_id}")
    print(f"{'='*60}")

    # Round 1-3: Ingest memories
    for i, memory in enumerate(user.memories, 1):
        print(f"\n[Round {i}] Ingesting: {memory[:50]}...")
        result = await ingest_memory(client, user, memory)
        print(f"  Result: {len(result.get('items', []))} items ingested")

    # Wait a bit for async processing
    print("\n[Waiting 2s for Mem0 async processing...]")
    await asyncio.sleep(2)

    # Search rounds
    for query in user.search_queries:
        print(f"\n[Search] Query: {query}")
        result = await search_memory(client, user, query)
        items = result.get("items", [])
        print(f"  Found {len(items)} results:")
        for item in items[:3]:
            text = item.get("content", {}).get("text", "")[:60]
            score = item.get("confidence", "N/A")
            print(f"    - [{score}] {text}...")


async def verify_isolation(client: httpx.AsyncClient) -> bool:
    """
    Verify tenant isolation:
    - Search with tenant-a credentials for tenant-b specific content
    - Should NOT find tenant-b's memories
    """
    print(f"\n{'='*60}")
    print("ISOLATION TEST: Verifying tenant separation")
    print(f"{'='*60}")

    # Tenant A user-1 searches for "swimming" (which is tenant-b/user-1's memory)
    tenant_a_user = TEST_USERS[0]  # tenant-a/user-1

    print(f"\n[Isolation] {tenant_a_user.tenant_id}/{tenant_a_user.user_id} searching for 'swimming in ocean'")
    print("  (This is tenant-b/user-1's memory, should NOT appear)")

    result = await search_memory(client, tenant_a_user, "swimming in the ocean")
    items = result.get("items", [])

    # Check if any result contains "swimming" or "ocean"
    leaked = False
    for item in items:
        text = item.get("content", {}).get("text", "").lower()
        if "swimming" in text or "ocean" in text:
            print(f"  ❌ LEAK DETECTED: {text}")
            leaked = True

    if not leaked:
        print("  ✅ No cross-tenant leakage detected")

    # Also verify tenant-b can find their own memories
    tenant_b_user = TEST_USERS[2]  # tenant-b/user-1
    print(f"\n[Isolation] {tenant_b_user.tenant_id}/{tenant_b_user.user_id} searching for 'swimming in ocean'")
    print("  (This IS their memory, should appear)")

    result = await search_memory(client, tenant_b_user, "swimming in the ocean")
    items = result.get("items", [])

    found_own = False
    for item in items:
        text = item.get("content", {}).get("text", "").lower()
        if "swimming" in text or "ocean" in text:
            print(f"  ✅ Found own memory: {text[:60]}...")
            found_own = True
            break

    if not found_own:
        print("  ⚠️ Could not find own memory (may be async delay)")

    return not leaked


async def main():
    print("="*60)
    print("Multi-Tenant Memory Engine Test")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Test users: {len(TEST_USERS)}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check health
        try:
            resp = await client.get(f"{BASE_URL}/health")
            resp.raise_for_status()
            print("✅ Server is healthy")
        except Exception as e:
            print(f"❌ Server not available: {e}")
            return

        # Run tests for each user
        for user in TEST_USERS:
            await run_user_test(client, user)

        # Wait for async processing
        print("\n[Waiting 3s for all async processing to complete...]")
        await asyncio.sleep(3)

        # Verify isolation
        isolation_ok = await verify_isolation(client)

        # Summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Users tested: {len(TEST_USERS)}")
        print(f"Tenant isolation: {'✅ PASS' if isolation_ok else '❌ FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
