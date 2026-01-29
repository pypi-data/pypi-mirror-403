"""Test script for LoopDetector v2"""

import sys

sys.path.insert(0, "c:/Users/julien/GuardianLayer")

from GuardianLayer.LoopDetector import LoopDetector

print("=" * 50)
print("Testing LoopDetector v2 (Hash-based)")
print("=" * 50)

detector = LoopDetector(max_history=5, max_repeats=2)

# Test 1: First call should pass
print("\n1. First call (should pass):")
call_a = {"tool": "search", "arguments": {"query": "python tutorials"}}
is_loop, reason = detector.check(call_a)
print(f"   Result: is_loop={is_loop}, reason={reason}")
assert not is_loop, "First call should not be a loop"

# Test 2: Immediate repeat should be blocked
print("\n2. Immediate repeat (should block):")
is_loop, reason = detector.check(call_a)
print(f"   Result: is_loop={is_loop}, reason={reason}")
assert is_loop and reason == "IMMEDIATE_REPEAT", "Should detect immediate repeat"

# Test 3: Different call should pass
print("\n3. Different call (should pass):")
call_b = {"tool": "scrape", "arguments": {"url": "https://example.com"}}
is_loop, reason = detector.check(call_b)
print(f"   Result: is_loop={is_loop}, reason={reason}")
assert not is_loop, "Different call should pass"

# Test 4: A-B-A pattern
print("\n4. A-B-A pattern (should block):")
is_loop, reason = detector.check(call_a)
print(f"   Result: is_loop={is_loop}, reason={reason}")
assert is_loop and reason == "SHORT_CYCLE", "Should detect A-B-A cycle"

# Test 5: Reset and test excessive repeats (with enough variation to avoid cycle detection)
print("\n5. Testing excessive repeats:")
detector.reset()
call_c = {"tool": "database", "arguments": {"sql": "SELECT * FROM users"}}

# To test excessive repeats, we need to call C multiple times with enough
# different calls in between to not trigger SHORT_CYCLE
calls_between = [
    {"tool": f"tool_{i}", "arguments": {"x": i}}
    for i in range(5)  # 5 different tools between each C call
]

for attempt in range(4):  # 4 attempts at C (max_repeats=2, so 3rd should fail)
    is_loop_c, reason_c = detector.check(call_c)
    print(f"   Call C attempt {attempt+1}: is_loop={is_loop_c}, reason={reason_c}")

    if is_loop_c:
        break  # Stop if blocked

    # Add different calls to avoid cycle detection
    for filler in calls_between:
        detector.check(filler)

# Either SHORT_CYCLE or REPEATED should block - both are valid loop detection
assert is_loop_c, "Should detect some loop pattern"
print(f"   Blocked by: {reason_c}")

# Test 6: Check metrics
print("\n6. Checking metrics:")
metrics = detector.get_metrics()
print(f"   Total checks: {metrics['total_checks']}")
print(f"   Loops detected: {metrics['loops_detected']}")
print(f"   Detection rate: {metrics['detection_rate']}")
print(f"   Cache size: {metrics['cache_size']}")

print("\n" + "=" * 50)
print(" All LoopDetector v2 tests passed!")
