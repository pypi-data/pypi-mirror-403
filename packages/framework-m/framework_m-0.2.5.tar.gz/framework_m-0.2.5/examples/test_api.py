"""Test script to call the API with httpx.

Usage:
    1. First start the server:
       cd /Users/ansh/Desktop/CastleCraft/m/libs/framework-m
       uv run python scripts/run_server.py

    2. Then in another terminal, run this script:
       cd /Users/ansh/Desktop/CastleCraft/m/libs/framework-m
       uv run python scripts/test_api.py
"""

import asyncio

import httpx


async def test_api() -> None:
    """Test the API endpoints."""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("Testing Framework M API")
        print("=" * 60)

        # Test 1: List todos (should be empty)
        print("\n1. GET /api/v1/Todo (list)")
        response = await client.get(f"{base_url}/api/v1/Todo")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        # Test 2: Create a todo (as Employee)
        print("\n2. POST /api/v1/Todo (create as Employee)")
        response = await client.post(
            f"{base_url}/api/v1/Todo",
            json={"title": "Test Todo"},
            headers={"x-user-id": "user123", "x-roles": "Employee"},
        )
        print(f"   Status: {response.status_code}")
        if response.status_code < 500:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Response: {response.text[:200]}")

        # Test 3: Create a todo without permission (as Guest)
        print("\n3. POST /api/v1/Todo (create as Guest - should fail)")
        response = await client.post(
            f"{base_url}/api/v1/Todo",
            json={"title": "Test Todo"},
            headers={"x-user-id": "guest", "x-roles": "Guest"},
        )
        print(f"   Status: {response.status_code}")
        if response.status_code < 500:
            print(f"   Response: {response.json()}")

        # Test 4: Get metadata
        print("\n4. GET /api/meta/Todo (metadata)")
        response = await client.get(f"{base_url}/api/meta/Todo")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   DocType: {data.get('doctype')}")
        print(f"   Has schema: {'schema' in data}")
        print(f"   Has layout: {'layout' in data}")
        print(f"   Has permissions: {'permissions' in data}")

        print("\n" + "=" * 60)
        print("API tests complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_api())
