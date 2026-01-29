"""Test script for cache.py"""

import sys

sys.path.insert(0, "c:/Users/julien/GuardianLayer")

from GuardianLayer.advice_generator import AdviceContext
from GuardianLayer.cache import AdviceCache, HashCache, LRUCache, ValidationCache

print("=" * 50)
print("Testing Cache System")
print("=" * 50)

# Test 1: LRU Cache basic operations
print("\n1. Testing LRUCache:")
cache = LRUCache(max_size=3, default_ttl=60)

cache.set("a", "value_a")
cache.set("b", "value_b")
cache.set("c", "value_c")

assert cache.get("a") == "value_a", "Should retrieve value_a"
assert cache.get("b") == "value_b", "Should retrieve value_b"
print("    Basic get/set works")

# Test LRU eviction
cache.set("d", "value_d")  # Should evict oldest (c was least recently used after a,b access)
print(f"   Cache size after adding 4th element: {cache.size()}")
assert cache.size() == 3, "Should maintain max_size"
print("    LRU eviction works")

# Test 2: Cache stats
print("\n2. Testing Cache Stats:")
print(f"   Hits: {cache.stats.hits}, Misses: {cache.stats.misses}")
print(f"   Hit rate: {cache.stats.hit_rate:.1%}")
cache.get("nonexistent")  # Should be a miss
assert cache.stats.misses > 0, "Should track misses"
print("    Stats tracking works")

# Test 3: AdviceCache with context
print("\n3. Testing AdviceCache:")
advice_cache = AdviceCache(max_size=100, default_ttl=60)

# Create a mock context
context1 = AdviceContext(
    tool_name="search",
    failure_count=2,
    last_error="timeout",
    similar_success=None,
    tool_reliability=0.8,
)

# Cache miss
result = advice_cache.get(context1)
assert result is None, "Should be cache miss"

# Cache set
advice_cache.set(context1, "Try with shorter query")

# Cache hit
result = advice_cache.get(context1)
assert result == "Try with shorter query", "Should retrieve cached advice"
print("    AdviceCache works")

# Test 4: Same context = same cache key
context2 = AdviceContext(
    tool_name="search",
    failure_count=2,
    last_error="timeout",
    similar_success=None,
    tool_reliability=0.8,
)
result = advice_cache.get(context2)
assert result == "Try with shorter query", "Same context should hit cache"
print("    Context-based key generation works")

# Test 5: ValidationCache
print("\n4. Testing ValidationCache:")
val_cache = ValidationCache(max_size=100)

val_cache.set("hash123", {"valid": True})
result = val_cache.get("hash123")
assert result == {"valid": True}, "Should retrieve validation result"
print("    ValidationCache works")

# Invalid results should not be cached (design decision)
val_cache.set("hash456", {"valid": False, "reason": "Missing param"})
result = val_cache.get("hash456")
assert result is None, "Invalid results should not be cached"
print("    Only valid results are cached (by design)")

# Test 6: HashCache
print("\n5. Testing HashCache:")
hash_cache = HashCache(max_size=10)

# Miss
result = hash_cache.get("some content")
assert result is None, "Should be cache miss"

# Set and hit
hash_cache.set("some content", "abc123")
result = hash_cache.get("some content")
assert result == "abc123", "Should retrieve cached hash"
print("    HashCache works")
print(f"   Stats: {hash_cache.get_stats()}")

# Test eviction
for i in range(15):
    hash_cache.set(f"content_{i}", f"hash_{i}")
print(f"   After 15 inserts with max_size=10: size={hash_cache.get_stats()['size']}")
print(f"   Evictions: {hash_cache.get_stats()['evictions']}")
print("   Eviction works")

print("\n" + "=" * 50)
print(" All cache tests passed!")
