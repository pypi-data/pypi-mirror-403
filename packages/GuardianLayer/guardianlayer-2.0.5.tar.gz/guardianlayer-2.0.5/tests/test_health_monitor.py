"""Test script for health_monitor.py"""

import sys

sys.path.insert(0, "c:/Users/julien/GuardianLayer")

from GuardianLayer.health_monitor import ErrorClassifier, ErrorType, HealthMonitor

# Test Error Classifier
print("=" * 50)
print("Testing ErrorClassifier")
print("=" * 50)

ec = ErrorClassifier()

tests = [
    ("Connection timeout", ErrorType.SYSTEM),
    ("Missing required parameter: sql", ErrorType.USER),
    ("Resource not found", ErrorType.BUSINESS),
    ("Random unknown error", ErrorType.UNKNOWN),
    ("503 Service Unavailable", ErrorType.SYSTEM),
    ("Invalid format for date", ErrorType.USER),
]

all_passed = True
for error_msg, expected in tests:
    result = ec.classify(error_msg)
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_passed = False
    print(f"  {status} '{error_msg}' -> {result.value} (expected: {expected.value})")

# Test Health Monitor
print("\n" + "=" * 50)
print("Testing HealthMonitor")
print("=" * 50)

hm = HealthMonitor(failure_threshold=3, base_cooldown=5)

# Initial check
result = hm.check_tool("test_api")
print(f"\n1. Initial check: allowed={result['allowed']}, score={result['health_score']}")

# Simulate user errors (should not penalize heavily)
print("\n2. Simulating 5 user errors (bad params):")
for i in range(5):
    hm.report_result("test_api", success=False, error_message="Missing parameter: query")
    health = hm.get_health("test_api")
    print(f"   After error {i+1}: score={health.score}, state={health.state.value}")

result = hm.check_tool("test_api")
print(f"   Tool still allowed: {result['allowed']} (user errors don't trip circuit)")

# Reset and test system errors
print("\n3. Testing with system errors (should trip circuit):")
hm.reset_tool("test_api")
for i in range(4):
    hm.report_result("test_api", success=False, error_message="Connection timeout")
    health = hm.get_health("test_api")
    print(f"   After error {i+1}: score={health.score}, state={health.state.value}")

result = hm.check_tool("test_api")
print(f"   Tool allowed after 4 system errors: {result['allowed']}")
if not result["allowed"]:
    print(f"   Retry after: {result.get('retry_after', 'N/A')}s")

# Test recovery
print("\n4. Testing success recovery:")
hm.reset_tool("test_api")
hm.report_result("test_api", success=True)
health = hm.get_health("test_api")
print(f"   After 1 success: score={health.score}")

print("\n" + "=" * 50)
if all_passed:
    print(" All tests passed!")
else:
    print(" Some tests failed")
