"""Test script for Multi-Level Experience Layer"""

import os
import sys

sys.path.insert(0, "c:/Users/julien/GuardianLayer")

from GuardianLayer.experience_layer import ExperienceLayer

DB_PATH = "test_experience.db"

# Cleanup previous run
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

print("=" * 50)
print("Testing Multi-Level Experience Layer")
print("=" * 50)

# Initialize Layer
exp = ExperienceLayer(db_path=DB_PATH)
session1_id = exp.current_session.session_id
print(f"Session 1 ID: {session1_id}")

# 1. Test Session Stats (L1)
print("\n1. Testing Session Stats (L1):")
call_a = {"tool": "search", "arguments": {"query": "A"}}
exp.log_incident(call_a, success=False, error_reason="Timeout")
exp.log_incident(call_a, success=True)

stats = exp.get_session_stats()
print(f"   Stats: {stats}")
assert stats["successes"] == 1, "Should have 1 success"
assert stats["failures"] == 1, "Should have 1 failure"
assert stats["tool_usage"]["search"] == 2, "Should have 2 calls to search"
print("    Session stats correct")

# 2. Test Process Cache (L2) - Collective Intelligence
print("\n2. Testing Process Cache (L2):")
# We logged a success for call_a above, so find_similar_success should return it
# even if we are in a new session (Process memory)

# Start new session
sid2 = exp.start_new_session()
print(f"   Started Session 2: {sid2}")
assert exp.get_session_stats()["successes"] == 0, "New session should be empty"

# Check if we remember the success from Session 1
similar = exp.find_similar_success("search")
print(f"   Found similar: {similar}")
assert similar is not None, "Should remember success from previous session (Process Memory)"
assert similar["arguments"]["query"] == "A", "Should be call A"
print("    Process cache works (Cross-session memory)")

# 3. Test Global Persistence (L3)
print("\n3. Testing Global Persistence (L3):")
# Close and reopen to simulate restart
import asyncio
asyncio.run(exp.close())
del exp

print("   Restarting ExperienceLayer...")
exp_new = ExperienceLayer(db_path=DB_PATH)

# Check if we still remember the success
similar_persistent = exp_new.find_similar_success("search")
print(f"   Found similar after restart: {similar_persistent}")
assert similar_persistent is not None, "Should remember success from DB (Global Memory)"
assert similar_persistent["arguments"]["query"] == "A", "Should be call A"

# Check tool reliability from DB
reliability = exp_new.get_tool_reliability("search")
print(f"   Reliability: {reliability:.1%}")
assert reliability == 0.5, "Should range 50% (1 success, 1 failure)"

print("    Global persistence works")

asyncio.run(exp_new.close())
# Cleanup
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

print("\n" + "=" * 50)
print(" All Experience Layer tests passed!")
