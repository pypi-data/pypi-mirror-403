"""Test script for Metrics Collector"""

import sys

sys.path.insert(0, "c:/Users/julien/GuardianLayer")

from GuardianLayer.guardian import GuardianLayer

print("=" * 50)
print("Testing Metrics & Observability")
print("=" * 50)

# Initialize
guardian = GuardianLayer(db_path=":memory:")

# 1. Test Loop Prevention ROI
print("\n1. Testing Loop Prevention ROI:")
call_a = {"tool": "search", "arguments": {"query": "A"}}

# Create a loop
guardian.check(call_a)
guardian.check(call_a)
result = guardian.check(call_a)  # Threshold reached
assert result["allowed"] == False, "Detailed check: Loop should be blocked"

metrics = guardian.get_metrics()
print(f"   ROI Stats: {metrics['roi']}")
prevented = metrics["roi"]["protection_events"]["loops_prevented"]
tokens = metrics["roi"]["estimated_savings"]["tokens_saved"]
print(f"   Prevented: {prevented}")
print(f"   Tokens saved: {tokens}")

assert prevented > 0, "Should track prevention events"
assert tokens > 0, "Should estimate saved tokens"
print("    Loop ROI tracking works")

# 2. Test Component Aggregation
print("\n2. Testing Component Aggregation:")
assert "loop_detection" in metrics, "Should have loop metrics"
assert "tool_health" in metrics, "Should have health metrics"
assert "session" in metrics, "Should have session metrics"

print(f"   Session ID: {metrics['session'].get('session_id')}")
assert metrics["session"].get("session_id") is not None
print("    Aggregation works")

# 3. Test Reset
print("\n3. Testing Metrics Reset:")
guardian.reset()
new_metrics = guardian.get_metrics()
new_prevented = new_metrics["roi"]["protection_events"]["loops_prevented"]
print(f"   Prevented after reset: {new_prevented}")
assert new_prevented == 0, "Metrics should be reset"

print("\n" + "=" * 50)
print("All Metrics tests passed!")
