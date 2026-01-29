import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from GuardianLayer.LoopDetector import LoopDetector

detector = LoopDetector()

# Test 1: First call OK

call1 = {"tool": "search", "query": "test"}
result1 = detector.check(call1)
print(f"Premier appel : {result1}")  # Devrait être (False, None)

# Test 2: Immediate repeat

result2 = detector.check(call1)
print(f"Deuxième appel : {result2}")  # Should be (True, "IMMEDIATE_REPEAT")


print(" It works !")
