"""
Performance Optimization Examples for pyWATS.

Demonstrates usage of:
1. Enhanced TTL caching for static data
2. Connection pooling (automatic in HTTP client)
3. Request coalescing for bulk operations
4. MessagePack serialization for large datasets
"""

import asyncio
from datetime import datetime
from typing import List

from pywats import pyWATS
from pywats.core.cache import AsyncTTLCache
from pywats.core.coalesce import ChunkedProcessor, coalesce_map
from pywats.core.performance import Serializer, benchmark_serialization


# =============================================================================
# Example 1: Enhanced Caching for Static Data
# =============================================================================

async def example_enhanced_caching():
    """Demonstrate enhanced TTL caching for process data."""
    print("\n" + "="*60)
    print("Example 1: Enhanced TTL Caching")
    print("="*60)
    
    api = pyWATS()
    
    # Process service uses AsyncTTLCache automatically
    # First call - cache miss, fetches from server
    print("\nFirst call (cache miss):")
    start = datetime.now()
    processes = await api.process.get_processes()
    duration = (datetime.now() - start).total_seconds() * 1000
    print(f"✓ Fetched {len(processes)} processes in {duration:.1f} ms")
    
    # Second call - cache hit, instant
    print("\nSecond call (cache hit):")
    start = datetime.now()
    processes = await api.process.get_processes()
    duration = (datetime.now() - start).total_seconds() * 1000
    print(f"✓ Fetched {len(processes)} processes in {duration:.1f} ms")
    
    # View cache statistics
    print(f"\nCache stats: {api.process.cache_stats}")
    
    # Force refresh if needed
    print("\nForcing cache refresh:")
    await api.process.refresh()
    print("✓ Cache refreshed")


# =============================================================================
# Example 2: Connection Pooling (Automatic)
# =============================================================================

async def example_connection_pooling():
    """Demonstrate connection pooling benefits."""
    print("\n" + "="*60)
    print("Example 2: Connection Pooling")
    print("="*60)
    
    api = pyWATS()
    
    # Connection pooling is automatic in AsyncHttpClient
    # It reuses connections for multiple requests
    
    print("\nMaking 10 concurrent requests:")
    start = datetime.now()
    
    tasks = []
    for i in range(10):
        # Each request reuses pooled connections
        task = api.product.get_product(f"PART-{i:03d}")
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = (datetime.now() - start).total_seconds() * 1000
    
    successful = sum(1 for r in results if not isinstance(r, Exception))
    print(f"✓ Completed {successful}/10 requests in {duration:.1f} ms")
    print(f"  Average: {duration/10:.1f} ms per request")
    print("\nNote: Connection pooling automatically reused connections")


# =============================================================================
# Example 3: Request Coalescing for Bulk Operations
# =============================================================================

async def example_request_coalescing():
    """Demonstrate request coalescing for bulk operations."""
    print("\n" + "="*60)
    print("Example 3: Request Coalescing")
    print("="*60)
    
    api = pyWATS()
    
    # Generate list of part numbers
    part_numbers = [f"PART-{i:05d}" for i in range(100)]
    
    # Method 1: ChunkedProcessor - process known list in chunks
    print("\nMethod 1: ChunkedProcessor (100 items in chunks of 20)")
    
    async def fetch_products_chunk(pns: List[str]) -> List:
        """Fetch multiple products in one call."""
        # In a real implementation, this would be a bulk API call
        # For now, we'll use gather as placeholder
        tasks = [api.product.get_product(pn) for pn in pns]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    processor = ChunkedProcessor(
        process_func=fetch_products_chunk,
        chunk_size=20,
        max_concurrent=5
    )
    
    start = datetime.now()
    results = await processor.process_all(part_numbers)
    duration = (datetime.now() - start).total_seconds()
    
    print(f"✓ Processed {len(part_numbers)} items in {duration:.1f}s")
    print(f"  Chunks: 5 (20 items each)")
    print(f"  Max concurrent chunks: 5")
    
    # Method 2: coalesce_map - simple concurrent mapping
    print("\nMethod 2: coalesce_map (with concurrency control)")
    
    async def fetch_single_product(pn: str):
        return await api.product.get_product(pn)
    
    start = datetime.now()
    results = await coalesce_map(
        part_numbers[:50],  # First 50
        fetch_single_product,
        batch_size=10,
        max_concurrent=5
    )
    duration = (datetime.now() - start).total_seconds()
    
    print(f"✓ Processed 50 items in {duration:.1f}s")
    print(f"  Batch size: 10")
    print(f"  Max concurrent: 5")


# =============================================================================
# Example 4: MessagePack Serialization
# =============================================================================

async def example_msgpack_serialization():
    """Demonstrate MessagePack serialization for large datasets."""
    print("\n" + "="*60)
    print("Example 4: MessagePack Serialization")
    print("="*60)
    
    # Create sample data (simulating large report dataset)
    sample_reports = {
        'reports': [
            {
                'id': f'REPORT-{i:05d}',
                'partNumber': 'PCBA-001',
                'serialNumber': f'SN-{i:06d}',
                'operationType': 100,
                'status': 'P' if i % 10 != 0 else 'F',
                'testTime': 15.5 + (i % 20),
                'steps': [
                    {
                        'name': f'Test {j}',
                        'value': j * 1.5,
                        'lowLimit': 0,
                        'highLimit': 10,
                        'status': 'P'
                    }
                    for j in range(10)
                ]
            }
            for i in range(100)  # 100 reports with 10 steps each
        ]
    }
    
    # Compare formats
    print("\nComparing serialization formats:")
    print("-" * 60)
    
    serializer = Serializer()
    comparison = serializer.compare_sizes(sample_reports)
    
    for format_name, stats in comparison.items():
        size_kb = stats['size'] / 1024
        savings = stats.get('savings', 'N/A')
        print(f"{format_name:12s}: {size_kb:7.1f} KB  (savings: {savings})")
    
    # Benchmark serialization speed
    print("\nBenchmarking serialization performance:")
    print("-" * 60)
    benchmark_serialization(sample_reports)
    
    # Usage example
    print("\nUsage example:")
    print("-" * 60)
    
    # JSON (default)
    json_serializer = Serializer(format='json')
    json_bytes = json_serializer.dumps(sample_reports)
    print(f"JSON size: {len(json_bytes) / 1024:.1f} KB")
    
    # MessagePack (faster, smaller)
    try:
        msgpack_serializer = Serializer(format='msgpack')
        msgpack_bytes = msgpack_serializer.dumps(sample_reports)
        print(f"MessagePack size: {len(msgpack_bytes) / 1024:.1f} KB")
        print(f"Savings: {(1 - len(msgpack_bytes)/len(json_bytes)) * 100:.1f}%")
        
        # Deserialize
        restored = msgpack_serializer.loads(msgpack_bytes)
        print(f"✓ Successfully serialized and deserialized {len(restored['reports'])} reports")
    except Exception as e:
        print(f"⚠ MessagePack not available: {e}")
        print("  Install with: pip install msgpack")


# =============================================================================
# Example 5: Production Pattern - All Features Combined
# =============================================================================

async def example_production_pattern():
    """Demonstrate production-ready pattern with all optimizations."""
    print("\n" + "="*60)
    print("Example 5: Production Pattern (All Features Combined)")
    print("="*60)
    
    # Initialize API with optimized settings
    api = pyWATS()
    
    print("\n1. Using cached static data (processes, operation types)")
    # Get operation types (cached automatically)
    operations = await api.process.get_test_operations()
    print(f"   ✓ Loaded {len(operations)} operation types (cached)")
    
    print("\n2. Batch processing reports")
    # Simulate batch report submission
    serial_numbers = [f"SN-{i:06d}" for i in range(20)]
    
    async def submit_report(sn: str):
        """Create and submit a report."""
        report = api.report.create_uut_report(
            operator="BatchTest",
            part_number="BATCH-001",
            revision="A",
            serial_number=sn,
            operation_type=100
        )
        
        root = report.get_root_sequence_call()
        root.add_numeric_step(
            name="Voltage",
            value=5.0,
            low_limit=4.5,
            high_limit=5.5,
            unit="V"
        )
        
        # Submit (uses connection pooling automatically)
        return await api.report.submit_async(report)
    
    start = datetime.now()
    results = await batch_map(
        serial_numbers,
        submit_report,
        batch_size=5,
        max_concurrent=3
    )
    duration = (datetime.now() - start).total_seconds()
    
    successful = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   ✓ Submitted {successful}/{len(serial_numbers)} reports in {duration:.1f}s")
    
    print("\n3. Cache statistics")
    print(f"   Process cache: {api.process.cache_stats}")
    
    print("\n✓ Production pattern complete")
    print("\nKey optimizations applied:")
    print("  • TTL caching for static data (processes, types)")
    print("  • Connection pooling (automatic, 100 max connections)")
    print("  • Request batching (controlled concurrency)")
    print("  • HTTP/2 multiplexing enabled")


# =============================================================================
# Run All Examples
# =============================================================================

async def run_all_examples():
    """Run all performance optimization examples."""
    print("\n" + "="*60)
    print("pyWATS Performance Optimization Examples")
    print("="*60)
    
    try:
        await example_enhanced_caching()
    except Exception as e:
        print(f"✗ Example 1 failed: {e}")
    
    try:
        await example_connection_pooling()
    except Exception as e:
        print(f"✗ Example 2 failed: {e}")
    
    try:
        await example_request_batching()
    except Exception as e:
        print(f"✗ Example 3 failed: {e}")
    
    try:
        await example_msgpack_serialization()
    except Exception as e:
        print(f"✗ Example 4 failed: {e}")
    
    try:
        await example_production_pattern()
    except Exception as e:
        print(f"✗ Example 5 failed: {e}")
    
    print("\n" + "="*60)
    print("Examples Complete")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_all_examples())
