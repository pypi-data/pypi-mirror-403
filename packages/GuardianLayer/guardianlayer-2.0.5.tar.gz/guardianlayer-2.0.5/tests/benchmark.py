import asyncio
import os
import statistics
import time

from GuardianLayer.guardian import GuardianLayer
from GuardianLayer.providers import AsyncSQLiteStorageProvider, SQLiteStorageProvider


def run_sync_benchmark(count=100):
    db_path = "bench_sync.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    storage = SQLiteStorageProvider(db_path)
    storage.init()
    guardian = GuardianLayer(storage_provider=storage)

    start = time.perf_counter()
    for i in range(count):
        guardian.check({"tool": "bench", "args": {"i": i}})
    end = time.perf_counter()

    try:
        if asyncio.iscoroutinefunction(guardian.experience.close):
            asyncio.run(guardian.experience.close())
        else:
            guardian.experience.close()
    except Exception:
        pass

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    return count / (end - start)


async def run_async_benchmark(count=100):
    db_path = "bench_async.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    storage = AsyncSQLiteStorageProvider(db_path)
    await storage.init()
    guardian = GuardianLayer(storage_provider=storage)

    start = time.perf_counter()
    tasks = [guardian.check_async({"tool": "bench", "args": {"i": i}}) for i in range(count)]
    await asyncio.gather(*tasks)
    end = time.perf_counter()

    await guardian.experience.close()
    await storage.close()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    return count / (end - start)


if __name__ == "__main__":
    print("Running Benchmarks...")

    # Warmup
    run_sync_benchmark(10)

    print("\n--- Sync Implementation (SQLAlchemy) ---")
    sync_rates = []
    for _ in range(5):
        rate = run_sync_benchmark(100)
        sync_rates.append(rate)
        print(f"Rate: {rate:.2f} ops/sec")

    avg_sync = statistics.mean(sync_rates)
    print(f"Average Sync Throughput: {avg_sync:.2f} ops/sec")

    print("\n--- Async Implementation (aiosqlite) ---")
    async_rates = []
    for _ in range(5):
        rate = asyncio.run(run_async_benchmark(100))
        async_rates.append(rate)
        print(f"Rate: {rate:.2f} ops/sec")

    avg_async = statistics.mean(async_rates)
    print(f"Average Async Throughput: {avg_async:.2f} ops/sec")

    speedup = avg_async / avg_sync if avg_sync > 0 else 0
    print(f"\n🚀 Speedup Factor: {speedup:.2f}x")
    if speedup > 1.5:
        print(" Async implementation provides significant throughput improvement.")
    else:
        print(" Warning: Async improvement is marginal (check overheads).")
