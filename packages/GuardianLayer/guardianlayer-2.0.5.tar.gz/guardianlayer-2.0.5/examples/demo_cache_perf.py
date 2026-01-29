"""
Cache Performance Demo - Shows the ROI of caching
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.guardian import GuardianLayer
from src.advice_generator import AdviceStyle

def main():
    print("=" * 60)
    print(" Cache Performance Demo")
    print("=" * 60)
    
    
    #We do not need persistence for this test
    guardian = GuardianLayer(
        db_path=None,  
        advice_style=AdviceStyle.CONCISE
    )
    
    # Register a tool
    guardian.ingest_tools([{
        "name": "search",
        "inputSchema": {
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    }])
    
    # Warm up - first call is always slower
    guardian.check({"tool": "search", "arguments": {"query": "warmup"}})
    guardian.report_result({"tool": "search", "arguments": {"query": "warmup"}}, success=True)
    
    # Test: 100 identical calls
    print("\n📊 Testing 100 identical validation calls...")
    
    call = {"tool": "search", "arguments": {"query": "test query"}}
    
    start = time.perf_counter()
    for _ in range(100):
        result = guardian.check(call)
        # Report success to generate advice context
        guardian.report_result(call, success=True)
    end = time.perf_counter()
    
    elapsed = (end - start) * 1000  # ms
    avg_per_call = elapsed / 100
    
    print(f"   Total time: {elapsed:.2f}ms")
    print(f"   Avg per call: {avg_per_call:.3f}ms")
    
    # Show cache stats
    print("\n📈 Cache Statistics:")
    
    # Advice cache
    advice_stats = guardian.advice_generator.get_cache_stats()
    if advice_stats:
        print(f"   Advice Cache:")
        print(f"     - Hit rate: {advice_stats['l1']['hit_rate']}")
        print(f"     - Hits: {advice_stats['l1']['hits']}, Misses: {advice_stats['l1']['misses']}")
    
    # Validation cache
    val_stats = guardian.mcp_facade.get_cache_stats()
    if val_stats:
        print(f"   Validation Cache:")
        print(f"     - Hit rate: {val_stats['hit_rate']}")
        print(f"     - Hits: {val_stats['hits']}, Misses: {val_stats['misses']}")
    
    # Loop detection cache
    loop_metrics = guardian.loop_detector.get_metrics()
    print(f"   Loop Detector Hash Cache:")
    print(f"     - Size: {loop_metrics['cache_size']}")
    
    # Test with varied calls
    print("\n📊 Testing 100 varied calls...")
    
    start = time.perf_counter()
    for i in range(100):
        call = {"tool": "search", "arguments": {"query": f"query_{i}"}}
        guardian.check(call)
    end = time.perf_counter()
    
    elapsed = (end - start) * 1000
    avg_per_call = elapsed / 100
    
    print(f"   Total time: {elapsed:.2f}ms")
    print(f"   Avg per call: {avg_per_call:.3f}ms")
    
    guardian.close()
    print("\n✅ Performance test complete!")


if __name__ == "__main__":
    main()
