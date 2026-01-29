"""
Async tests for GuardianLayer
"""


import pytest

from GuardianLayer.guardian import GuardianLayer
from GuardianLayer.providers import AsyncInMemoryCacheProvider, AsyncSQLiteStorageProvider


@pytest.mark.asyncio
async def test_guardian_async_basic():
    """Test basic async functionality"""
    # Create guardian with async providers
    async with AsyncSQLiteStorageProvider(":memory:") as storage:
        async with AsyncInMemoryCacheProvider() as cache:
            guardian = GuardianLayer(storage_provider=storage, cache_provider=cache)

            # Test async check
            tool_call = {"tool": "test_tool", "arguments": {"query": "test"}}
            result = await guardian.check_async(tool_call)

            assert result["allowed"] == True
            assert "health_score" in result
            assert "advice" in result
            assert result["is_probe"] == False


@pytest.mark.asyncio
async def test_loop_detector_async():
    """Test async loop detection"""
    from GuardianLayer.LoopDetector import LoopDetector

    detector = LoopDetector(max_history=5, max_repeats=2)

    call = {"tool": "test", "args": {"query": "test"}}

    # First call should be allowed
    is_loop, reason = await detector.check_async(call)
    assert is_loop == False
    assert reason is None

    # Second identical call should be blocked
    is_loop, reason = await detector.check_async(call)
    assert is_loop == True
    assert reason == "IMMEDIATE_REPEAT"


@pytest.mark.asyncio
async def test_mcp_facade_async():
    """Test async MCP validation"""
    from GuardianLayer.mcp_facade import MCPFacade

    facade = MCPFacade()

    # Register a test tool
    tools = [
        {
            "name": "test_tool",
            "description": "Test tool",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        }
    ]
    facade.ingest_mcp_tools(tools)

    # Test valid call
    call = {"tool": "test_tool", "arguments": {"query": "test"}}
    result = await facade.validate_call_async(call)
    assert result["valid"] == True

    # Test invalid call (missing required param)
    call = {"tool": "test_tool", "arguments": {}}
    result = await facade.validate_call_async(call)
    assert result["valid"] == False
    assert "Missing required parameter" in result["reason"]


@pytest.mark.asyncio
async def test_health_monitor_async():
    """Test async health monitoring"""
    from GuardianLayer.health_monitor import HealthMonitor

    monitor = HealthMonitor()

    # Test healthy tool
    result = await monitor.check_tool_async("test_tool")
    assert result["allowed"] == True
    assert result["health_score"] == 100
    assert result["is_probe"] == False


@pytest.mark.asyncio
async def test_async_provider_operations():
    """Test async provider operations"""
    # Test async cache provider
    cache = AsyncInMemoryCacheProvider(max_size=10)
    await cache.set("test_key", {"data": "test"})
    value = await cache.get("test_key")
    assert value == {"data": "test"}

    stats = await cache.get_stats()
    assert "hits" in stats or "size" in stats

    # Test async storage provider
    storage = AsyncSQLiteStorageProvider(":memory:")
    await storage.init()

    # Test logging incidents
    await storage.log_incident(
        {
            "session_id": "test_session",
            "tool_name": "test_tool",
            "fingerprint": "test_fp",
            "success": True,
            "timestamp": 1234567890,
            "error": None,
            "call_data": '{"test": "data"}',
        }

    )

    # Manually update best practices stats (since we are testing provider directly)
    await storage.update_best_practice(
        fingerprint="test_fp", tool_name="test_tool", success=True, call_data='{"test": "data"}'
    )

    # Test getting stats
    stats = await storage.get_tool_stats("test_tool")
    assert stats["successes"] == 1
    assert stats["failures"] == 0

    await storage.close()
