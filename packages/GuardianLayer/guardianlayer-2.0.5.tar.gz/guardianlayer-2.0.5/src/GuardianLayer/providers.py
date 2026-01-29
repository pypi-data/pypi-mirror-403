"""
Default Implementations for GuardianLayer Providers.
Batteries-included: SQLite Storage and In-Memory Cache.
"""

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from .cache import LRUCache
from .interfaces import (
    AsyncCacheProvider,
    AsyncStorageProvider,
    CacheProvider,
    StorageProvider,
)

logger = logging.getLogger(__name__)

Base = declarative_base()


class IncidentModel(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String)
    tool_name = Column(String, index=True)
    fingerprint = Column(String, index=True)
    success = Column(Boolean)
    timestamp = Column(Float)
    error_reason = Column(Text, nullable=True)
    context_hint = Column(Text, nullable=True)
    call_data = Column(Text, nullable=True)


class BestPracticeModel(Base):
    __tablename__ = "best_practices"
    fingerprint = Column(String, primary_key=True)
    tool_name = Column(String)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_success_data = Column(Text, nullable=True)


class InMemoryCacheProvider(CacheProvider):
    """Default cache using LRUCache implementation"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache = LRUCache(max_size=max_size, default_ttl=default_ttl)
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        with self._lock:
            # Note: LRUCache handles default_ttl internally if not overridden,
            # but current implementation might ignore per-call ttl depending on LRUCache structure.
            # Assuming basic set for now.
            self._cache.set(key, value, ttl)

    def delete(self, key: str):
        with self._lock:
            self._cache.delete(key)  # Assuming LRUCache now has a delete method

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            s = self._cache.stats
            return {"hits": s.hits, "misses": s.misses, "size": self._cache.size()}


class AsyncInMemoryCacheProvider(AsyncCacheProvider):
    """Async wrapper around LRUCache"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache = LRUCache(max_size=max_size, default_ttl=default_ttl)

    async def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        self._cache.set(key, value, ttl)

    async def delete(self, key: str):
        self._cache.delete(key)

    async def get_stats(self) -> Dict[str, Any]:
        s = self._cache.stats
        return {"hits": s.hits, "misses": s.misses, "size": self._cache.size()}

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"AsyncCache error: {exc_val}")


class SQLiteStorageProvider(StorageProvider):
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Thread-safe engine configuration
        self.engine = create_engine(
            f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._lock = Lock()  # Keep lock just in case for complex ops, though Session handles most

    def init(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

        # Optimize SQLite settings
        try:
            with self.engine.connect() as connection:
                connection.execute(text("PRAGMA journal_mode=WAL"))
                connection.execute(text("PRAGMA synchronous=NORMAL"))
        except Exception as e:
            logger.warning(f"Could not set SQLite pragmas: {e}")

    @contextmanager
    def _session(self):
        """Provide a transactional scope around a series of operations."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def log_incident(self, incident_data: Dict[str, Any]):
        with self._session() as session:
            incident = IncidentModel(
                session_id=incident_data.get("session_id"),
                tool_name=incident_data.get("tool_name"),
                fingerprint=incident_data.get("fingerprint"),
                success=bool(incident_data.get("success", False)),
                timestamp=incident_data.get("timestamp", time.time()),
                error_reason=incident_data.get("error_reason"),
                context_hint=incident_data.get("context_hint"),
                call_data=(
                    str(incident_data.get("call_data")) if incident_data.get("call_data") else None
                ),
            )
            session.add(incident)

    def update_best_practice(
        self, fingerprint: str, tool_name: str, success: bool, call_data: Optional[str]
    ):
        from sqlalchemy.dialects.sqlite import insert

        with self._session() as session:
            # Atomic UPSERT to prevent race conditions
            stmt = insert(BestPracticeModel).values(
                fingerprint=fingerprint,
                tool_name=tool_name,
                success_count=(1 if success else 0),
                failure_count=(0 if success else 1),
                last_success_data=(call_data if success else None),
            )

            # Logic: If exists, increment counters and update data if success
            set_dict = {
                "success_count": BestPracticeModel.success_count + (1 if success else 0),
                "failure_count": BestPracticeModel.failure_count + (0 if success else 1),
            }
            if success and call_data:
                set_dict["last_success_data"] = call_data

            stmt = stmt.on_conflict_do_update(index_elements=["fingerprint"], set_=set_dict)
            session.execute(stmt)

    def get_best_practice(self, tool_name: str) -> Optional[Dict[str, Any]]:
        with self._session() as session:
            # Find BestPractice with highest success count for this tool
            bp = (
                session.query(BestPracticeModel)
                .filter(BestPracticeModel.tool_name == tool_name)
                .filter(BestPracticeModel.success_count > 0)
                .order_by(BestPracticeModel.success_count.desc())
                .first()
            )

            if bp and bp.last_success_data:
                return {"last_success_data": bp.last_success_data}
            return None

    def get_tool_stats(self, tool_name: str) -> Dict[str, int]:
        with self._session() as session:
            # Sum success/failure counts
            result = (
                session.query(
                    func.sum(BestPracticeModel.success_count),
                    func.sum(BestPracticeModel.failure_count),
                )
                .filter(BestPracticeModel.tool_name == tool_name)
                .first()
            )

            successes = result[0] if result and result[0] else 0
            failures = result[1] if result and result[1] else 0

            return {"successes": successes, "failures": failures}

    def close(self):
        """Dispose of the engine connection pool"""
        self.engine.dispose()


class AsyncSQLiteStorageProvider(AsyncStorageProvider):
    """Async version of SQLite storage using aiosqlite"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    async def init(self):
        """Initialize async connection and create tables"""
        import aiosqlite

        self._conn = await aiosqlite.connect(self.db_path)
        # Enable WAL for concurrency compatibility with Sync provider
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA synchronous=NORMAL")

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                tool_name TEXT,
                fingerprint TEXT,
                success BOOLEAN,
                timestamp REAL,
                error_reason TEXT,
                context_hint TEXT,
                call_data TEXT
            )
        """)
        # Add indexes for performance (matching Sync)
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_name ON incidents(tool_name)")
        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_id ON incidents(session_id)"
        )

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS best_practices (
                fingerprint TEXT PRIMARY KEY,
                tool_name TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                last_success_data TEXT
                -- Note: 'last_updated' was in old schema but not in new Model.
                -- We'll omit it to stay consistent with SQLAlchemy model
                -- or add it to Model if needed. For now, strict match.
            )
        """)
        await self._conn.commit()

    async def log_incident(self, incident_data: Dict[str, Any]):
        """Log a raw incident record asynchronously"""
        if not self._conn:
            await self.init()

        await self._conn.execute(
            """
            INSERT INTO incidents (session_id, tool_name, fingerprint, success, timestamp, error_reason, context_hint, call_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                incident_data.get("session_id"),
                incident_data.get("tool_name"),
                incident_data.get("fingerprint"),
                incident_data.get("success"),
                incident_data.get("timestamp"),
                incident_data.get("error_reason"),  # Changed from 'error' to match model
                incident_data.get("context_hint"),
                incident_data.get("call_data"),
            ),
        )
        await self._conn.commit()

    async def update_best_practice(
        self, fingerprint: str, tool_name: str, success: bool, call_data: str
    ):
        """Update best practices record asynchronously"""
        if not self._conn:
            await self.init()

        # SQLite UPSERT syntax
        await self._conn.execute(
            """
            INSERT INTO best_practices (fingerprint, tool_name, success_count, failure_count, last_success_data)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
                success_count = success_count + ?,
                failure_count = failure_count + ?,
                last_success_data = CASE WHEN ? = 1 THEN ? ELSE last_success_data END
        """,
            (
                fingerprint,
                tool_name,
                1 if success else 0,
                0 if success else 1,
                call_data if success else None,
                # Update values
                1 if success else 0,
                0 if success else 1,
                1 if success else 0,
                call_data,
            ),
        )
        await self._conn.commit()

    async def get_best_practice(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve best successful call pattern asynchronously"""
        if not self._conn:
            await self.init()

        cursor = await self._conn.execute(
            """
            SELECT last_success_data FROM best_practices
            WHERE tool_name = ? AND success_count > 0
            ORDER BY success_count DESC
            LIMIT 1
        """,
            (tool_name,),
        )
        row = await cursor.fetchone()
        await cursor.close()

        if row:
            return {"last_success_data": row[0]}
        return None

    async def get_tool_stats(self, tool_name: str) -> Dict[str, int]:
        """Return global stats for a tool asynchronously"""
        if not self._conn:
            await self.init()

        cursor = await self._conn.execute(
            """
            SELECT
                SUM(success_count),
                SUM(failure_count)
            FROM best_practices WHERE tool_name = ?
        """,
            (tool_name,),
        )
        row = await cursor.fetchone()
        await cursor.close()

        # row is (successes, failures)
        if row:
            return {"successes": row[0] or 0, "failures": row[1] or 0}
        return {"successes": 0, "failures": 0}

    async def close(self):
        """Close async connection"""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def __aenter__(self):
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        if exc_type:
            logger.error(f"AsyncStorage error: {exc_val}")
