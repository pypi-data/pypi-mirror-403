#!/usr/bin/env python3
"""
Example: Using Memory Engine with Google ADK

This example demonstrates how to use the MemoryEngineAdapter
with Google ADK's Agent framework.

Prerequisites:
1. Memory Engine server running: uvicorn memory_engine.main:app --reload
2. Install google-adk: pip install google-adk

Usage:
    python adk_example.py
"""

import asyncio
import os
from dataclasses import dataclass
from typing import List, Any

# Import the adapter (canonical path)
from memory_engine_adapters.adk_adapter import MemoryEngineAdapter

# Simulate ADK types for demonstration
# In real usage, these come from google.adk


@dataclass
class MockEvent:
    """Simulated ADK Event for demonstration."""
    role: str
    content: str


@dataclass
class MockSession:
    """Simulated ADK Session for demonstration."""
    app_name: str
    user_id: str
    session_id: str
    events: List[MockEvent]
    state: dict


async def main():
    """Demonstrate Memory Engine ADK adapter usage."""

    # Configuration - adjust based on your Memory Engine setup
    MEMORY_ENGINE_URL = os.getenv("MEMORY_ENGINE_URL", "http://localhost:8000")
    MEMORY_ENGINE_TOKEN = os.getenv("MEMORY_ENGINE_TOKEN", "demo-token")
    TENANT_ID = os.getenv("TENANT_ID", "demo-tenant")

    print("=" * 60)
    print("Memory Engine ADK Adapter Example")
    print("=" * 60)

    # Create the adapter
    adapter = MemoryEngineAdapter(
        base_url=MEMORY_ENGINE_URL,
        token=MEMORY_ENGINE_TOKEN,
        tenant_id=TENANT_ID,
        ingest_mode="infer",  # Let Memory Engine extract memories from conversation
    )

    # Simulate a conversation session
    session = MockSession(
        app_name="demo-app",
        user_id="user-alice",
        session_id="session-001",
        events=[
            MockEvent(role="user", content="Hi! My name is Alice and I love coffee."),
            MockEvent(role="assistant", content="Nice to meet you, Alice! I'll remember that you love coffee."),
            MockEvent(role="user", content="I work as a software engineer at Google."),
            MockEvent(role="assistant", content="That's interesting! Software engineering at Google sounds exciting."),
            MockEvent(role="user", content="I prefer Python for backend development."),
            MockEvent(role="assistant", content="Python is a great choice for backend work!"),
        ],
        state={"mood": "friendly"},
    )

    print("\n1. Adding session to memory...")
    print(f"   User: {session.user_id}")
    print(f"   App: {session.app_name}")
    print(f"   Events: {len(session.events)}")

    try:
        await adapter.add_session_to_memory(session)
        print("   ✓ Session memories ingested successfully")
    except Exception as e:
        print(f"   ✗ Failed to ingest memories: {e}")
        return

    # Wait a moment for memories to be processed
    # (Mem0 Cloud needs ~3 minutes, but in-memory provider is instant)
    print("\n2. Waiting for memory processing...")
    await asyncio.sleep(1)

    # Search for memories
    print("\n3. Searching memories...")

    queries = [
        "What is the user's name?",
        "What does the user like to drink?",
        "Where does the user work?",
        "What programming language does the user prefer?",
    ]

    for query in queries:
        print(f"\n   Query: '{query}'")
        try:
            response = await adapter.search_memory(
                app_name="demo-app",
                user_id="user-alice",
                query=query,
                top_k=3,
            )

            if response.memories:
                for i, memory in enumerate(response.memories, 1):
                    for event in memory.events:
                        content = event.get("content", "")[:100]
                        print(f"   Result {i}: {content}...")
            else:
                print("   No memories found")

        except Exception as e:
            print(f"   ✗ Search failed: {e}")

    # Clean up
    await adapter.close()
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


async def demo_with_real_adk():
    """
    Example showing integration with real Google ADK.

    This requires google-adk to be installed.
    Uncomment and adapt as needed.
    """
    """
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    # Create Memory Engine adapter
    memory_service = MemoryEngineAdapter(
        base_url="http://localhost:8000",
        token="your-token",
        tenant_id="your-tenant",
        ingest_mode="infer",
    )

    # Define your agent
    agent = Agent(
        model="gemini-2.0-flash",
        name="memory-demo-agent",
        instruction="You are a helpful assistant with long-term memory.",
    )

    # Create runner with memory service
    runner = Runner(
        agent=agent,
        app_name="memory-demo",
        session_service=InMemorySessionService(),
        memory_service=memory_service,  # Inject our adapter
    )

    # Run the agent
    session = await runner.session_service.create_session(
        app_name="memory-demo",
        user_id="user-123",
    )

    async for event in runner.run_async(
        user_id="user-123",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text="Hello! Remember that I like tea.")]
        ),
    ):
        if event.is_final_response():
            print(f"Agent: {event.content.text}")

    # Session memories will be automatically added when session ends
    """
    pass


if __name__ == "__main__":
    asyncio.run(main())
