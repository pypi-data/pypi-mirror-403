"""
Interfaces for GuardianLayer Dependency Injection.
Allows users to bring their own Storage (DB) and Cache backends.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class CacheProvider(ABC):
    """Abstract interface for caching backends (Redis, Memcached, Memory, etc.)"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Store a value with optional TTL in seconds."""
        pass

    @abstractmethod
    def delete(self, key: str):
        """Remove a value."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Return implementation-specific stats (hits, misses, size)."""
        pass


class StorageProvider(ABC):
    """Abstract interface for persistent storage (SQLite, Postgres, etc.)"""

    @abstractmethod
    def init(self):
        """Initialize connections (create tables if needed)."""
        pass

    @abstractmethod
    def log_incident(self, incident_data: Dict[str, Any]):
        """
        Log a raw incident record.
        incident_data contains: session_id, tool_name, fingerprint, success, timestamp, error, etc.
        """
        pass

    @abstractmethod
    def update_best_practice(self, fingerprint: str, tool_name: str, success: bool, call_data: str):
        """
        Update the 'collective intelligence' or best practices record.
        Should handle incrementing counters and updating last_success_data.
        """
        pass

    @abstractmethod
    def get_best_practice(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the best successful call pattern for a tool.
        Returns dict with 'last_success_data' or None.
        """
        pass

    @abstractmethod
    def get_tool_stats(self, tool_name: str) -> Dict[str, int]:
        """
        Return global stats for a tool.
        Returns: {'successes': int, 'failures': int}
        """
        pass

    @abstractmethod
    def close(self):
        """Close connection."""
        pass


class AsyncCacheProvider(ABC):
    """Async version of CacheProvider interface"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Store a value with optional TTL in seconds."""
        pass

    @abstractmethod
    async def delete(self, key: str):
        """Remove a value."""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Return implementation-specific stats (hits, misses, size)."""
        pass


class AsyncStorageProvider(ABC):
    """Async version of StorageProvider interface"""

    @abstractmethod
    async def init(self):
        """Initialize connections (create tables if needed)."""
        pass

    @abstractmethod
    async def log_incident(self, incident_data: Dict[str, Any]):
        """
        Log a raw incident record.
        incident_data contains: session_id, tool_name, fingerprint, success, timestamp, error, etc.
        """
        pass

    @abstractmethod
    async def update_best_practice(
        self, fingerprint: str, tool_name: str, success: bool, call_data: str
    ):
        """
        Update the 'collective intelligence' or best practices record.
        Should handle incrementing counters and updating last_success_data.
        """
        pass

    @abstractmethod
    async def get_best_practice(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the best successful call pattern for a tool.
        Returns dict with 'last_success_data' or None.
        """
        pass

    @abstractmethod
    async def get_tool_stats(self, tool_name: str) -> Dict[str, int]:
        """
        Return global stats for a tool.
        Returns: {'successes': int, 'failures': int}
        """
        pass

    @abstractmethod
    async def close(self):
        """Close connection."""
        pass
