"""
Intelligent Cache System - Multi-Level Caching for Performance
L1: Local memory (instant)
L2: Redis (optional, for multi-instance sharing)
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry:
    """A cached value with metadata"""

    value: Any
    timestamp: float
    hits: int = 0


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": f"{self.hit_rate:.1%}",
        }


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache with TTL support.
    Thread-safe for single-writer scenarios.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: list = []  # For LRU tracking
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache, returns None if not found or expired"""
        if key not in self._cache:
            self.stats.misses += 1
            return None

        entry = self._cache[key]
        now = time.time()

        # Check TTL
        if now - entry.timestamp > self.default_ttl:
            # Expired
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self.stats.misses += 1
            return None

        # Update access order (LRU)
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        entry.hits += 1
        self.stats.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set a value in cache"""
        now = time.time()

        # Evict if at capacity
        while len(self._cache) >= self.max_size:
            self._evict_oldest()

        self._cache[key] = CacheEntry(value=value, timestamp=now, hits=0)

        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def delete(self, key: str):
        """Delete a key from cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)

    def _evict_oldest(self):
        """Remove the least recently used entry"""
        if self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self.stats.evictions += 1

    def clear(self):
        """Clear all entries"""
        self._cache.clear()
        self._access_order.clear()

    def size(self) -> int:
        """Current number of entries"""
        return len(self._cache)


class AdviceCache:
    """
    Intelligent cache for generated advice.
    Avoids regenerating the same advice for similar contexts.

    Features:
    - L1: Local LRU cache (instant, in-memory)
    - L2: Redis (optional, for multi-instance sharing)
    - Context-aware key generation
    - TTL with shorter expiry for critical advice
    """

    def __init__(self, max_size: int = 500, default_ttl: int = 3600, redis_client=None):
        """
        Initialize the advice cache.

        Args:
            max_size: Max entries in L1 cache
            default_ttl: Default TTL in seconds
            redis_client: Optional Redis client for L2 caching
        """
        self._l1 = LRUCache(max_size=max_size, default_ttl=default_ttl)
        self._redis = redis_client
        self._redis_prefix = "guardian:advice:"
        self._default_ttl = default_ttl

    def _compute_key(self, context) -> str:
        """Generate a unique cache key from an AdviceContext"""
        key_data = {
            "tool": context.tool_name,
            "failures": context.failure_count,
            "reliability": context.tool_reliability,
            "error": context.last_error[:50] if context.last_error else None,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def get(self, context) -> Optional[str]:
        """
        Get cached advice for a context.
        Checks L1 first, then L2 (Redis).
        """
        key = self._compute_key(context)

        # L1: Local cache
        cached = self._l1.get(key)
        if cached is not None:
            return cached

        # L2: Redis (if available)
        if self._redis:
            try:
                redis_key = f"{self._redis_prefix}{key}"
                cached = self._redis.get(redis_key)
                if cached:
                    # Warm L1 cache
                    self._l1.set(key, cached)
                    self._l1.stats.hits += 1  # Count as L2 hit
                    return cached
            except Exception as e:
                logger.debug(f"Redis get failed: {e}")

        return None

    def set(self, context, advice: str):
        """
        Cache advice for a context.
        Stores in L1 and optionally L2.
        """
        if not advice:
            return  # Don't cache empty advice

        key = self._compute_key(context)

        # Determine TTL based on criticality
        # Critical advice (high failure count) expires faster
        ttl = 300 if context.failure_count >= 3 else self._default_ttl

        # L1: Local cache
        self._l1.set(key, advice)

        # L2: Redis (if available)
        if self._redis:
            try:
                redis_key = f"{self._redis_prefix}{key}"
                self._redis.setex(redis_key, ttl, advice)
            except Exception as e:
                logger.debug(f"Redis set failed: {e}")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "l1": self._l1.stats.to_dict(),
            "l1_size": self._l1.size(),
            "l2_enabled": self._redis is not None,
        }

    def clear(self):
        """Clear L1 cache"""
        self._l1.clear()


class ValidationCache:
    """
    Cache for MCP validation results.
    Avoids re-validating the same tool calls repeatedly.
    """

    def __init__(self, max_size: int = 2000, ttl: int = 1800):
        """
        Initialize the validation cache.

        Args:
            max_size: Max entries (validations are cheap, keep more)
            ttl: TTL in seconds (30 minutes default)
        """
        self._cache = LRUCache(max_size=max_size, default_ttl=ttl)

    def get(self, fingerprint: str) -> Optional[Dict]:
        """Get cached validation result"""
        return self._cache.get(fingerprint)

    def set(self, fingerprint: str, result: Dict):
        """Cache a validation result"""
        # Only cache valid results (invalid ones may be fixed)
        if result.get("valid", False):
            self._cache.set(fingerprint, result)

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {**self._cache.stats.to_dict(), "size": self._cache.size()}


class HashCache:
    """
    Cache for computed hashes.
    Prevents recomputing SHA-256 for the same tool calls.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize hash cache.

        Args:
            max_size: Max entries to keep
        """
        self._cache: Dict[str, str] = {}
        self._max_size = max_size
        self.stats = CacheStats()

    def get(self, content: str) -> Optional[str]:
        """Get cached hash for content"""
        if content in self._cache:
            self.stats.hits += 1
            return self._cache[content]
        self.stats.misses += 1
        return None

    def set(self, content: str, hash_value: str):
        """Cache a hash value"""
        # Simple eviction: clear half when full
        if len(self._cache) >= self._max_size:
            keys = list(self._cache.keys())[: self._max_size // 2]
            for key in keys:
                del self._cache[key]
                self.stats.evictions += 1

        self._cache[content] = hash_value

    def get_stats(self) -> Dict:
        return {**self.stats.to_dict(), "size": len(self._cache)}
