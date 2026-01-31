# Thread Safety in pyWATS

## Overview

pyWATS uses both threading and asyncio for concurrent operations. This guide explains the thread safety guarantees and best practices for using pyWATS in multi-threaded environments.

## Thread-Safe Components

### MemoryQueue

**Status:** ✅ Fully thread-safe

All methods can be called concurrently from multiple threads without external synchronization.

```python
from pywats.queue import MemoryQueue

# Safe to use from multiple threads
queue = MemoryQueue()

# Thread 1
item = queue.add({"data": "from_thread_1"})

# Thread 2 (concurrent access is safe)
next_item = queue.get_next()
```

**Lock type:** `threading.RLock` (reentrant)

**What's protected:**
- All queue mutations (add, update, remove)
- All query operations (size, count_by_status)
- Iteration (returns snapshot to avoid holding lock)

**Important:** Individual `QueueItem` objects are NOT thread-safe once retrieved. Use `queue.update(item)` to safely persist changes:

```python
# ✅ CORRECT
item = queue.get_next()
item.mark_processing()
queue.update(item)  # Thread-safe update

# ❌ INCORRECT
item = queue.get_next()
item.status = QueueItemStatus.COMPLETED  # Race condition if other threads access same item
# Missing queue.update(item)
```

### TTLCache

**Status:** ✅ Fully thread-safe

All cache operations are protected by a lock and can be called from multiple threads.

```python
from pywats.core.cache import TTLCache

# Safe for concurrent access
cache = TTLCache[str](default_ttl=3600)

# Multiple threads can safely:
cache.set("key1", "value1")  # Thread 1
value = cache.get("key2")     # Thread 2
cache.cleanup_expired()       # Thread 3
```

**Lock type:** `threading.RLock` (reentrant)

**Performance tip:** For very high concurrency (>100 req/s), consider sharding:

```python
class ShardedCache:
    """Reduce lock contention with multiple cache instances."""
    
    def __init__(self, num_shards=16, **kwargs):
        self._shards = [TTLCache(**kwargs) for _ in range(num_shards)]
        self._num_shards = num_shards
    
    def _get_shard(self, key: str):
        return self._shards[hash(key) % self._num_shards]
    
    def get(self, key: str, default=None):
        return self._get_shard(key).get(key, default)
    
    def set(self, key: str, value, ttl=None):
        self._get_shard(key).set(key, value, ttl)
```

### parallel_execute()

**Status:** ✅ Thread pool based

Uses `ThreadPoolExecutor` for concurrent execution.

```python
from pywats.core.parallel import parallel_execute

# Execute multiple API calls concurrently
results = parallel_execute(
    keys=["PN-001", "PN-002", "PN-003"],
    operation=lambda pn: api.product.get_product(pn),
    max_workers=10
)
```

**Thread pool:** Default 10 workers, configurable up to 100

**IMPORTANT:** Your `operation` function must be thread-safe:

```python
# ✅ SAFE - No shared state
def get_product(pn: str):
    return api.product.get_product(pn)

# ❌ UNSAFE - Shared mutable state
results = {}  # Shared!
def unsafe_operation(pn: str):
    results[pn] = api.product.get_product(pn)  # Race condition!
    return results[pn]

# ✅ SAFE - Proper locking
import threading
results = {}
lock = threading.Lock()

def safe_operation(pn: str):
    product = api.product.get_product(pn)
    with lock:
        results[pn] = product
    return product
```

### EventBus

**Status:** ✅ Thread-safe

Uses `queue.Queue` (thread-safe) and `ThreadPoolExecutor` for event processing.

```python
from pywats_events.bus import EventBus

bus = EventBus(max_workers=10)
bus.start()

# Safe to publish from any thread
bus.publish(Event.create(EventType.TEST_RESULT, payload=data))
```

**Implementation:**
- Uses thread-safe `queue.Queue` for event queuing
- Background worker thread processes events
- Handlers executed in thread pool

## Async-Safe Components

### AsyncTTLCache

**Status:** ✅ Async-safe

Use with `async`/`await` syntax only. Do NOT mix sync and async access.

```python
from pywats.core.cache import AsyncTTLCache

cache = AsyncTTLCache[str](default_ttl=3600)

# ✅ CORRECT - Async access
async def get_cached_data():
    value = await cache.get_async("key")
    if value is None:
        value = await fetch_data()
        await cache.set_async("key", value)
    return value

# ❌ INCORRECT - Mixing sync and async
async def mixed_access():
    await cache.get_async("key")  # Async
    cache.get("key")              # Sync - creates overhead
```

### AsyncEventBus

**Status:** ✅ Fully async

All methods are coroutines. Concurrency controlled by `asyncio.Semaphore`.

```python
from pywats_events.bus import AsyncEventBus

bus = AsyncEventBus(max_concurrency=10)
await bus.start()

# Publish events asynchronously
await bus.publish_async(event)
```

### AsyncPendingQueue & AsyncConverterPool

**Status:** ✅ Watchdog integration correct

These components use file system watching with proper thread-safe signaling:

```python
# Internal implementation (you don't need to do this):
def _on_file_queued(self, file_path: Path) -> None:
    """Handle new file (called from watchdog thread)."""
    # ✅ CORRECT: Uses call_soon_threadsafe
    if self._loop and self._loop.is_running():
        self._loop.call_soon_threadsafe(self._new_file_event.set)
```

**Why this matters:** Watchdog runs in a separate thread. You cannot directly call async methods from a sync thread. The code uses `call_soon_threadsafe()` to safely signal the async event loop.

## Mixing Sync and Async

### run_sync() Function

Bridges async code to sync contexts safely:

```python
from pywats.core.sync_runner import run_sync

async def async_operation():
    return await some_async_call()

# Call from sync code:
result = run_sync(async_operation())
```

**How it works:**
- If no event loop is running: uses `asyncio.run()`
- If event loop is already running: uses thread pool to avoid blocking

**Thread safety:** Uses a pooled `ThreadPoolExecutor` (4 workers) to avoid overhead of creating threads repeatedly.

## Best Practices

### 1. Use High-Level Primitives

✅ **DO:**
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(process_item, items)
```

❌ **DON'T:**
```python
import threading

threads = []
for item in items:
    t = threading.Thread(target=process_item, args=(item,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
```

### 2. Always Use Context Managers for Locks

✅ **DO:**
```python
with lock:
    shared_data.append(item)
```

❌ **DON'T:**
```python
lock.acquire()
shared_data.append(item)
lock.release()  # Might not run if exception occurs!
```

### 3. Avoid Shared Mutable State

✅ **DO:**
```python
def parallel_operation(key: str) -> Result:
    # No shared state - thread-safe by design
    return process(key)

results = parallel_execute(keys, parallel_operation)
```

❌ **DON'T:**
```python
results = {}  # Shared mutable state

def parallel_operation(key: str):
    results[key] = process(key)  # Race condition!
```

### 4. Use Thread-Safe Collections

✅ **DO:**
```python
from queue import Queue

q = Queue()  # Thread-safe

# Thread 1
q.put(item)

# Thread 2
item = q.get()
```

❌ **DON'T:**
```python
items = []  # NOT thread-safe

# Thread 1
items.append(item)  # Race condition!

# Thread 2
item = items.pop()  # Race condition!
```

### 5. Document Thread Safety Requirements

✅ **DO:**
```python
def process_batch(items: List[Item]) -> None:
    """Process items in batch.
    
    Thread Safety:
        This function is NOT thread-safe. Do not call
        concurrently for the same batch instance.
    """
    # ... implementation
```

### 6. Test Concurrent Access

Always test thread safety for critical components:

```python
import threading

def test_concurrent_cache_access():
    """Test cache under concurrent load."""
    cache = TTLCache[str](default_ttl=60)
    
    def worker(thread_id):
        for i in range(100):
            key = f"key_{i % 10}"
            cache.set(key, f"value_{thread_id}_{i}")
            value = cache.get(key)
            assert value is not None
    
    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(10)
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Verify no crashes or data corruption
    assert cache.size <= 10
```

## Common Pitfalls

### ❌ Pitfall #1: Mutating Retrieved Queue Items

```python
# WRONG
item = queue.get_next()
item.status = QueueItemStatus.COMPLETED  # Not thread-safe!

# CORRECT
item = queue.get_next()
item.mark_completed()  # Safe mutation
queue.update(item)      # Thread-safe persistence
```

### ❌ Pitfall #2: Creating ThreadPoolExecutor in Loop

```python
# WRONG - Creates/destroys threads repeatedly
for item in items:
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(process, item)

# CORRECT - Reuse executor
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(process, item) for item in items]
    for future in as_completed(futures):
        result = future.result()
```

### ❌ Pitfall #3: Mixing Sync/Async Cache Access

```python
cache = AsyncTTLCache[str]()

# WRONG - Creates dual locking overhead
async def mixed():
    await cache.get_async("key")  # Async lock
    cache.get("key")              # + Sync lock = overhead!

# CORRECT - Use one or the other
async def async_only():
    await cache.get_async("key")  # Only async lock
```

### ❌ Pitfall #4: Sharing HTTP Clients Without Checking Thread Safety

```python
# WRONG - httpx.Client is NOT thread-safe
client = httpx.Client()

def fetch(url):
    return client.get(url)  # Race condition!

with ThreadPoolExecutor() as executor:
    executor.map(fetch, urls)  # ❌ UNSAFE

# CORRECT - Create client per thread OR use async
async with httpx.AsyncClient() as client:
    tasks = [client.get(url) for url in urls]
    results = await asyncio.gather(*tasks)  # ✅ SAFE
```

## Platform Compatibility

All threading code in pyWATS uses Python standard library primitives that work identically across platforms:

| Platform | Status | Notes |
|----------|--------|-------|
| **Windows** | ✅ Fully supported | Uses native Windows threading |
| **Linux** | ✅ Fully supported | Uses POSIX threads (pthreads) |
| **macOS** | ✅ Fully supported | Uses POSIX threads (pthreads) |
| **BSD** | ✅ Fully supported | Uses POSIX threads (pthreads) |

**No platform-specific code is used** - all threading relies on Python's cross-platform abstractions.

## Performance Considerations

### Lock Contention

**MemoryQueue:**
- Lock scope: Minimal (single operation)
- Expected contention: Low
- Scales well up to ~100 concurrent threads

**TTLCache:**
- Lock scope: Hash lookup + update
- Expected contention: Low to medium
- For >100 req/s: consider sharding (see example above)

**ThreadPoolExecutor:**
- Internal locking optimized by standard library
- Scales well to hundreds of concurrent tasks

### When to Use Threading vs Asyncio

**Use Threading when:**
- CPU-bound operations (with multiprocessing)
- Blocking I/O that doesn't support async
- Integrating with thread-based libraries

**Use Asyncio when:**
- I/O-bound operations (network, disk)
- Many concurrent connections (>100)
- Event-driven architectures

**Mixed approach (pyWATS):**
- Core API: Async-first design
- Sync wrappers: Use `run_sync()` for compatibility
- Background processing: Threading for file watching, etc.

## Summary

✅ **Thread-Safe Components:**
- MemoryQueue - All methods
- TTLCache - All methods
- EventBus - All methods
- parallel_execute - Executor itself (operation must be thread-safe)

✅ **Async-Safe Components:**
- AsyncTTLCache - Use async methods only
- AsyncEventBus - Fully async
- AsyncPendingQueue/AsyncConverterPool - Watchdog integration correct

✅ **Cross-Platform:**
- 100% compatible (Windows, Linux, macOS, BSD)
- No platform-specific code

⚠️ **Watch Out For:**
- Mutating QueueItem objects without queue.update()
- Sharing non-thread-safe clients in parallel_execute
- Mixing sync/async on AsyncTTLCache
- Creating executors in loops

## Additional Resources

- [Python Threading Documentation](https://docs.python.org/3/library/threading.html)
- [Python Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)
- [Threading Best Practices](https://realpython.com/intro-to-python-threading/)
