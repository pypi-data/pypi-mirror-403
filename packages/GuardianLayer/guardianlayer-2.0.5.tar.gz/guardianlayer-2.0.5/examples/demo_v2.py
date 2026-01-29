"""
GuardianLayer v2.0 Demo - Smart Circuit Breaker with Auto-Recovery
Shows the new health monitoring features.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.guardian import GuardianLayer
from src.advice_generator import AdviceStyle

def main():
    print("=" * 60)
    print("  GuardianLayer v2.0 Demo - Smart Circuit Breaker.")
    print("=" * 60)
    
    # Initialize with short cooldown for demo
    
    guardian = GuardianLayer(
        db_path="demo_v2.db",
        max_repeats=2,
        advice_style=AdviceStyle.EXPERT,
        failure_threshold=3,  # Open circuit after 3 system failures
        base_cooldown=5       # 5 second cooldown for demo
    )
    
    # Simulate MCP tool registration
    mcp_tools = [
        {
            "name": "unstable_api",
            "description": "An API that sometimes fails",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    ]
    
    guardian.ingest_tools(mcp_tools)
    print(f"\n📥 Registered tools: {mcp_tools[0]['name']}")
    
    # ===== Scenario: System Errors vs User Errors =====
    print("\n" + "-" * 50)
    print("Scenario 1: User Errors (bad params) - Should NOT trip circuit")
    print("-" * 50)
    
    for i in range(5):
        call = {"tool": "unstable_api", "arguments": {"query": f"test_{i}"}}
        result = guardian.check(call)
        if result["allowed"]:
            # Report user error (bad parameter)
            guardian.report_result(call, success=False, 
                                   error="Missing required parameter: format")
        
        health = guardian.health_monitor.get_health("unstable_api")
        print(f"  After user error {i+1}: score={health.score}, state={health.state.value}")
    
    print(f" Circuit still CLOSED after 5 user errors!")
    
    # ===== Scenario: System Errors =====
    print("\n" + "-" * 50)
    print("Scenario 2: System Errors (timeout) - Should trip circuit")
    print("-" * 50)
    
    guardian.reset_tool("unstable_api")  # Reset for clean test
    
    for i in range(4):
        call = {"tool": "unstable_api", "arguments": {"query": f"sys_test_{i}"}}
        result = guardian.check(call)
        
        if result["allowed"]:
            # Report system error (timeout)
            guardian.report_result(call, success=False, 
                                   error="Connection timeout after 30s")
            health = guardian.health_monitor.get_health("unstable_api")
            print(f"  After system error {i+1}: score={health.score}, state={health.state.value}")
        else:
            print(f" BLOCKED: {result['reason']}")
            if result.get('retry_after'):
                print(f"     Retry after: {result['retry_after']:.1f}s") 
    
    # ===== Scenario: Auto-Recovery =====
    print("\n" + "-" * 50)
    print("Scenario 3: Auto-Recovery (waiting for cooldown)")
    print("-" * 50)
    
    print("  ⏳ Waiting 6 seconds for cooldown to expire...")
    time.sleep(6)
    
    # Try again - should be in HALF_OPEN
    call = {"tool": "unstable_api", "arguments": {"query": "recovery_test"}}
    result = guardian.check(call)
    print(f"  After cooldown: allowed={result['allowed']}, is_probe={result['is_probe']}")
    print(f"  Advice: {result.get('advice', 'None')}")
    
    # Report success - should close circuit
    guardian.report_result(call, success=True)
    health = guardian.health_monitor.get_health("unstable_api")
    print(f"  After success: score={health.score}, state={health.state.value}")
    
    # ===== Show Metrics =====
    print("\n" + "-" * 50)
    print("Metrics (ROI Visibility)")
    print("-" * 50)
    
    metrics = guardian.get_metrics()
    
    print("\n  ROI (New!):")
    roi = metrics['roi']
    print(f"    - Uptime: {roi['uptime_seconds']}s")
    print(f"    - Loops Prevented: {roi['protection_events']['loops_prevented']}")
    print(f"    - Circuit Breaks: {roi['protection_events']['circuit_breaks']}")
    print(f"    - Tokens Saved (Est): {roi['estimated_savings']['tokens_saved']}")
    
    print(f"\n  Loop Detection:")
    print(f"    - Total checks: {metrics['loop_detection']['total_checks']}")
    print(f"    - Loops blocked: {metrics['loop_detection']['loops_detected']}")
    
    print(f"\n  Session Stats (New!):")
    session = metrics['session']
    print(f"    - ID: {session['session_id']}")
    print(f"    - Duration: {session['duration']}")
    print(f"    - Success/Fail: {session['successes']}/{session['failures']}")
    
    print(f"\n  Tool Health:")
    for tool, health in metrics['tool_health'].items():
        print(f"    - {tool}: {health['score']}% health, {health['state']}")
    
    guardian.close()
    print("\n  Demo complete!")


if __name__ == "__main__":
    main()
