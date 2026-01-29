"""
GuardianLayer Demo - Simulating an AI Agent with Self-Awareness
This demo shows how GuardianLayer prevents infinite loops and learns from failures.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.guardian import GuardianLayer
from src.advice_generator import AdviceStyle

def main():
    print("=" * 60)
    print("🛡️  GuardianLayer Demo - AI Meta-Cognition Shield")
    print("=" * 60)
    
    # Initialize with SQLite persistence
    guardian = GuardianLayer(
        db_path="demo_experience.db",
        max_repeats=2,
        advice_style=AdviceStyle.EXPERT
    )
    
    # Simulate MCP tool registration
    mcp_tools = [
        {
            "name": "web_search",
            "description": "Search the web",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "database_query",
            "description": "Query the database",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string"},
                    "limit": {"type": "integer"}
                },
                "required": ["sql"]
            }
        }
    ]
    
    print("\n📥 Ingesting MCP tools...")
    count = guardian.ingest_tools(mcp_tools)
    print(f"   Registered {count} tools\n")
    
    # ===== Scenario 1: Normal Call =====
    print("-" * 40)
    print("Scenario 1: Normal tool call")
    print("-" * 40)
    
    call1 = {"tool": "web_search", "arguments": {"query": "Python tutorials"}}
    result = guardian.check(call1)
    print(f"Call: {call1}")
    print(f"Allowed: {result['allowed']}")
    
    # Simulate success
    guardian.report_result(call1, success=True)
    print(" Reported as SUCCESS\n")
    
    # ===== Scenario 2: Missing Parameter =====
    print("-" * 40)
    print("Scenario 2: Missing required parameter")
    print("-" * 40)
    
    call2 = {"tool": "database_query", "arguments": {}}  # Missing 'sql'
    result = guardian.check(call2)
    print(f"Call: {call2}")
    print(f"Allowed: {result['allowed']}")
    print(f"Reason: {result['reason']}")
    print(f"Suggestion: {result['suggestion']}\n")
    
    # ===== Scenario 3: Loop Detection =====
    print("-" * 40)
    print("Scenario 3: The AI starts looping...")
    print("-" * 40)
    
    bad_call = {"tool": "web_search", "arguments": {"query": "impossible task"}}
    
    for i in range(4):
        result = guardian.check(bad_call)
        print(f"Attempt {i+1}: Allowed={result['allowed']}, Reason={result.get('reason', 'OK')}")
        if result['allowed']:
            guardian.report_result(bad_call, success=False, error="No results found")
    
    # ===== Scenario 4: Circuit Breaker =====
    print("\n" + "-" * 40)
    print("Scenario 4: Circuit Breaker activates")
    print("-" * 40)
    
    fragile_call = {"tool": "database_query", "arguments": {"sql": "SELECT * FROM broken"}}
    
    for i in range(6):
        result = guardian.check(fragile_call)
        if result['allowed']:
            guardian.report_result(fragile_call, success=False, error="Connection timeout")
            print(f"Attempt {i+1}: Allowed, but FAILED")
        else:
            print(f"Attempt {i+1}: BLOCKED! {result['reason']}")
    
    # ===== Show Awareness Context =====
    print("\n" + "-" * 40)
    print("Self-Awareness Context (for prompt injection)")
    print("-" * 40)
    print(guardian.get_awareness_context())
    
    # ===== Show Tool Reliability =====
    print("-" * 40)
    print("Tool Reliability Scores")
    print("-" * 40)
    for tool in ["web_search", "database_query"]:
        reliability = guardian.experience.get_tool_reliability(tool)
        if reliability is not None:
            print(f"  {tool}: {reliability:.1%}")
    
    guardian.close()
    print("\n  Demo complete!")


if __name__ == "__main__":
    main()
