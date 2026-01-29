"""
Test script for Custom Providers (Infrastructure Independent)
Demonstrates how to implement and inject custom Storage and Cache backends.
"""

import sys
from typing import Any, Dict, Optional

sys.path.insert(0, "c:/Users/julien/GuardianLayer")

from GuardianLayer.guardian import GuardianLayer
from GuardianLayer.interfaces import CacheProvider, StorageProvider

print("=" * 50)
print("Testing Custom Providers (BYO-DB/Cache)")
print("=" * 50)


# 1. Define Custom Cache (e.g., Simulated Redis)
class MockRedisCache(CacheProvider):
    def __init__(self):
        self.data = {}
        print("  MockRedisCache initialized")

    def get(self, key: str) -> Optional[Any]:
        return self.data.get(key)

    def set(self, key: str, value: Any, ttl: int = None):
        self.data[key] = value

    def delete(self, key: str):
        if key in self.data:
            del self.data[key]

    def get_stats(self) -> Dict:
        return {"keys": len(self.data)}


# 2. Define Custom Storage (e.g., Simulated Postgres)
class MockPostgresStorage(StorageProvider):
    def __init__(self):
        self.incidents = []
        print("    MockPostgresStorage initialized")

    def init(self):
        print("    Connecting to Mock Postgres...")

    def log_incident(self, incident_data: Dict):
        print(f"    [MOCK DB] Logging incident for {incident_data['tool_name']}")
        self.incidents.append(incident_data)

    def update_best_practice(self, fingerprint, tool_name, success, call_data):
        pass  # Mock implementation

    def get_best_practice(self, tool_name):
        return None

    def get_tool_stats(self, tool_name):
        return {"successes": 0, "failures": 0}

    def close(self):
        print("   🔌 Closing Mock Postgres")


# 3. Inject into GuardianLayer
print("\nInstantiating GuardianLayer with custom providers...")
my_cache = MockRedisCache()
my_db = MockPostgresStorage()

guardian = GuardianLayer(storage_provider=my_db, cache_provider=my_cache)

# 4. Verify Usage
print("\nRunning check...")
# This should trigger a cache set (MockRedis) and potentially DB access
call = {"tool": "test_tool", "arguments": {"x": 1}}
guardian.check(call)

# Store something in cache manually via advice generator?
# The check() call generates advice. AdviceGenerator uses cache.
# Let's check our mock cache.
print(f"   Cache keys: {my_cache.data.keys()}")
# Might be empty if no advice generated or no cache hit yet.

# Let's force a report_result to test DB
print("\nReporting result...")
guardian.report_result(call, success=False, error="Test Error")

# Verify DB
assert len(my_db.incidents) == 1
assert my_db.incidents[0]["tool_name"] == "test_tool"
print("    Custom Storage used successfully")

guardian.close()

print("\n" + "=" * 50)
print(" Infrastructure Agnosticism Verified!")
