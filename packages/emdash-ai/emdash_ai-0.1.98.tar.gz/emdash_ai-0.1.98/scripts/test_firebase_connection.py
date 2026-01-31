#!/usr/bin/env python3
"""Smoke test for Firebase multiuser connection.

Usage:
    python3 scripts/test_firebase_connection.py
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
import httpx

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


async def main():
    print("=" * 60)
    print("Firebase Multiuser Connection Smoke Test")
    print("=" * 60)
    print()

    # Check environment variables
    print("[1/5] Checking environment variables...")

    project_id = os.environ.get("FIREBASE_PROJECT_ID")
    database_url = os.environ.get("FIREBASE_DATABASE_URL")
    api_key = os.environ.get("FIREBASE_API_KEY")
    credentials_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    multiuser_enabled = os.environ.get("EMDASH_MULTIUSER_ENABLED")
    multiuser_provider = os.environ.get("EMDASH_MULTIUSER_PROVIDER")

    missing = []
    if not multiuser_enabled:
        missing.append("EMDASH_MULTIUSER_ENABLED")
    if not multiuser_provider:
        missing.append("EMDASH_MULTIUSER_PROVIDER")
    if not project_id:
        missing.append("FIREBASE_PROJECT_ID")
    if not database_url:
        missing.append("FIREBASE_DATABASE_URL")
    if not api_key and not credentials_path:
        missing.append("FIREBASE_API_KEY or FIREBASE_CREDENTIALS_PATH")

    if missing:
        print(f"  ✗ Missing: {', '.join(missing)}")
        print("\nPlease set these in your .env file")
        return False

    auth_type = "API_KEY" if api_key else "CREDENTIALS_PATH"
    print(f"  ✓ EMDASH_MULTIUSER_ENABLED = {multiuser_enabled}")
    print(f"  ✓ EMDASH_MULTIUSER_PROVIDER = {multiuser_provider}")
    print(f"  ✓ FIREBASE_PROJECT_ID = {project_id}")
    print(f"  ✓ FIREBASE_DATABASE_URL = {database_url}")
    print(f"  ✓ Auth method: {auth_type}")
    print()

    # Normalize database URL
    if database_url and not database_url.endswith("/"):
        database_url = database_url.rstrip("/")

    # Build URL helper
    def db_url(path: str) -> str:
        path = path.lstrip("/")
        return f"{database_url}/{path}.json"

    # Get auth params
    def get_auth_params() -> dict:
        if api_key:
            return {"key": api_key}
        return {}

    # Test connection
    print("[2/5] Connecting to Firebase...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Try to read root to test connection
            url = db_url("")
            params = get_auth_params()
            response = await client.get(url, params=params)

            if response.status_code == 404:
                print("  ✗ Database not found - did you create the Realtime Database?")
                print(f"    URL: {database_url}")
                print("    Go to Firebase Console → Build → Realtime Database → Create Database")
                return False
            elif response.status_code == 401:
                print("  ✗ Authentication failed - check your API key")
                return False
            elif response.status_code != 200:
                print(f"  ✗ Unexpected status: {response.status_code}")
                print(f"    Response: {response.text}")
                return False

            print("  ✓ Connected to Firebase")
        except httpx.ConnectError as e:
            print(f"  ✗ Connection error: {e}")
            print("    Check your FIREBASE_DATABASE_URL")
            return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
        print()

        # Test write operation
        print("[3/5] Testing write operation...")
        test_path = "_smoke_test"
        test_data = {
            "test": True,
            "timestamp": "smoke_test",
            "message": "Hello from emdash!"
        }
        try:
            url = db_url(test_path)
            params = get_auth_params()
            response = await client.put(url, json=test_data, params=params)

            if response.status_code == 401:
                print("  ✗ Write unauthorized - check database rules")
                print("    Go to Firebase Console → Realtime Database → Rules")
                print('    Set rules to: {"rules": {".read": true, ".write": true}}')
                return False
            elif response.status_code != 200:
                print(f"  ✗ Write failed: {response.status_code}")
                print(f"    Response: {response.text}")
                return False

            print(f"  ✓ Write successful to /{test_path}")
        except Exception as e:
            print(f"  ✗ Write error: {e}")
            return False
        print()

        # Test read operation
        print("[4/5] Testing read operation...")
        try:
            url = db_url(test_path)
            params = get_auth_params()
            response = await client.get(url, params=params)
            response.raise_for_status()

            read_data = response.json()
            if read_data == test_data:
                print("  ✓ Read successful - data matches")
            else:
                print("  ⚠ Read successful but data mismatch")
                print(f"    Expected: {test_data}")
                print(f"    Got: {read_data}")
        except Exception as e:
            print(f"  ✗ Read error: {e}")
            return False
        print()

        # Cleanup
        print("[5/5] Cleaning up...")
        try:
            url = db_url(test_path)
            params = get_auth_params()
            await client.delete(url, params=params)
            print(f"  ✓ Deleted /{test_path}")
        except Exception as e:
            print(f"  ⚠ Cleanup warning: {e}")

    print()
    print("=" * 60)
    print("✓ All tests passed! Firebase connection is working.")
    print("=" * 60)
    print()
    print("You can now use multiuser features:")
    print("  /share  - Create a shared session")
    print("  /join   - Join a session with invite code")
    print("  /who    - See who's in the session")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
