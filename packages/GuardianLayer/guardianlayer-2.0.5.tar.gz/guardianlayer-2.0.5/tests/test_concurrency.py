import os
import threading
from concurrent.futures import ThreadPoolExecutor

from GuardianLayer.guardian import GuardianLayer
from GuardianLayer.health_monitor import HealthMonitor


def test_concurrent_checks_thread_safe():
    """Test 100 threads simultanés checking calls on GuardianLayer"""
    # Use a file-based DB for more realistic contention than :memory: in some cases,
    # but :memory: is fine for basic locking checks.
    # To be safe and fast, let's use a temp db file.
    db_path = "test_concurrent.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # Initialize guardian
    guardian = GuardianLayer(db_path=db_path)

    # We expect 1000 calls total
    total_calls = 1000

    def worker(i):
        # Simulate different tools to spread load
        tool_name = f"tool_{i % 5}"
        call = {"tool": tool_name, "args": {"i": i}}

        # 1. Check
        result = guardian.check(call)

        # 2. Report result (simulating execution)
        # Random success/failure
        success = i % 3 != 0
        guardian.report_result(call, success, error="Simulated error" if not success else None)

        return result

    try:
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(worker, i) for i in range(total_calls)]
            # Wait for all
            for f in futures:
                f.result()

        # Verify metrics
        metrics = guardian.get_metrics()
        loop_stats = metrics["loop_detection"]

        # Ideally, we should have processed all checks
        assert loop_stats["total_checks"] == total_calls

        # Check health monitor consistency
        health = guardian.health_monitor.get_all_health()

        # Note: Health monitor updates happen in report_result
        # Just ensure no exceptions occurred and data looks plausible
        assert len(health) > 0

    finally:
        guardian.close()
        if os.path.exists(db_path):
            os.remove(db_path)


def test_health_monitor_locking():
    """Verify detailed locking in HealthMonitor"""
    monitor = HealthMonitor()

    target_count = 1000

    def stress_test():
        for i in range(target_count):
            monitor.report_result("stress_tool", (i % 2 == 0))
            monitor.check_tool("stress_tool")

    ws = []
    for _ in range(10):
        t = threading.Thread(target=stress_test)
        ws.append(t)
        t.start()

    for w in ws:
        w.join()

    # Verify consistency
    health = monitor.get_health("stress_tool")
    # 10 threads * 1000 calls = 10000 total calls reported
    assert health.total_calls == 10 * target_count
    print("Health Monitor Locking Test Passed")


if __name__ == "__main__":
    print("Running Concurrency Tests...")
    try:
        test_concurrent_checks_thread_safe()
        print("Guardian Concurrent Checks Test Passed")
        test_health_monitor_locking()
        print("All Concurrency Tests Passed ")
    except Exception as e:
        print(f"Tests Failed : {e}")
        import traceback

        traceback.print_exc()
