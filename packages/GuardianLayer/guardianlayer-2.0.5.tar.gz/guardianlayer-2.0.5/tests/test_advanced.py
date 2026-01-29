import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from GuardianLayer.LoopDetector import LoopDetector


def test_immediate_repeat():
    detector = LoopDetector()
    call = {"tool": "search", "arguments": {"query": "test"}}

    # First call OK
    assert detector.check(call) == (False, None)

    # Second call = loop
    is_loop, reason = detector.check(call)
    assert is_loop == True
    assert reason == "IMMEDIATE_REPEAT"


def test_different_calls():
    detector = LoopDetector()
    call1 = {"tool": "search", "arguments": {"query": "A"}}
    call2 = {"tool": "search", "arguments": {"query": "B"}}

    # Two differents calls = OK
    assert detector.check(call1) == (False, None)
    assert detector.check(call2) == (False, None)


def test_cycle_detection():
    detector = LoopDetector()
    call_a = {"tool": "search", "arguments": {"query": "A"}}
    call_b = {"tool": "scrape", "arguments": {"url": "B"}}
    call_c = {"tool": "db", "arguments": {"sql": "C"}}

    detector.check(call_a)  # A
    detector.check(call_b)  # B
    detector.check(call_c)  # C

    # A -> B -> C -> A (cycle detected)
    is_loop, reason = detector.check(call_a)
    assert is_loop == True
    assert "CYCLE" in reason
