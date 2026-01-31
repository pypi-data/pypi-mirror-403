"""
Performance optimization utilities for pyWATS.

Provides optional high-performance features:
- MessagePack serialization (faster than JSON)
- Compression support
- Streaming utilities for large datasets
"""
from typing import Any, Optional, Union
import json
import logging

logger = logging.getLogger(__name__)

# Optional msgpack support
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False
    logger.debug("msgpack not available - install with: pip install msgpack")

# Optional compression support
try:
    import gzip
    import zlib
    COMPRESSION_AVAILABLE = True
except ImportError:
    COMPRESSION_AVAILABLE = False


class Serializer:
    """
    High-performance serialization with multiple format support.
    
    Supports:
    - JSON (default, universal compatibility)
    - MessagePack (faster, smaller, requires msgpack library)
    - Compressed JSON (for large payloads)
    
    Example:
        >>> serializer = Serializer(format='msgpack')
        >>> data = {'reports': [...]}  # Large dataset
        >>> serialized = serializer.dumps(data)
        >>> restored = serializer.loads(serialized)
    """
    
    FORMATS = ['json', 'msgpack', 'json-gzip']
    
    def __init__(
        self,
        format: str = 'json',
        compress_threshold: int = 10000  # bytes
    ):
        """
        Initialize serializer.
        
        Args:
            format: Serialization format ('json', 'msgpack', 'json-gzip')
            compress_threshold: Compress JSON if larger than this (bytes)
        """
        if format not in self.FORMATS:
            raise ValueError(f"Invalid format: {format}. Choose from {self.FORMATS}")
        
        if format == 'msgpack' and not MSGPACK_AVAILABLE:
            logger.warning(
                "msgpack not available, falling back to json. "
                "Install with: pip install msgpack"
            )
            format = 'json'
        
        if format == 'json-gzip' and not COMPRESSION_AVAILABLE:
            logger.warning("gzip not available, falling back to json")
            format = 'json'
        
        self.format = format
        self.compress_threshold = compress_threshold
    
    def dumps(self, data: Any) -> bytes:
        """
        Serialize data to bytes.
        
        Args:
            data: Data to serialize
            
        Returns:
            Serialized bytes
        """
        if self.format == 'msgpack':
            return self._dumps_msgpack(data)
        elif self.format == 'json-gzip':
            return self._dumps_json_gzip(data)
        else:  # json
            return self._dumps_json(data)
    
    def loads(self, data: bytes) -> Any:
        """
        Deserialize data from bytes.
        
        Args:
            data: Serialized bytes
            
        Returns:
            Deserialized data
        """
        if self.format == 'msgpack':
            return self._loads_msgpack(data)
        elif self.format == 'json-gzip':
            return self._loads_json_gzip(data)
        else:  # json
            return self._loads_json(data)
    
    def _dumps_json(self, data: Any) -> bytes:
        """Serialize to JSON."""
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        return json_str.encode('utf-8')
    
    def _loads_json(self, data: bytes) -> Any:
        """Deserialize from JSON."""
        return json.loads(data.decode('utf-8'))
    
    def _dumps_msgpack(self, data: Any) -> bytes:
        """Serialize to MessagePack."""
        if not MSGPACK_AVAILABLE:
            raise RuntimeError("msgpack not available")
        return msgpack.packb(data, use_bin_type=True)
    
    def _loads_msgpack(self, data: bytes) -> Any:
        """Deserialize from MessagePack."""
        if not MSGPACK_AVAILABLE:
            raise RuntimeError("msgpack not available")
        return msgpack.unpackb(data, raw=False)
    
    def _dumps_json_gzip(self, data: Any) -> bytes:
        """Serialize to compressed JSON."""
        if not COMPRESSION_AVAILABLE:
            raise RuntimeError("gzip not available")
        
        json_bytes = self._dumps_json(data)
        
        # Only compress if above threshold
        if len(json_bytes) < self.compress_threshold:
            return json_bytes
        
        return gzip.compress(json_bytes)
    
    def _loads_json_gzip(self, data: bytes) -> Any:
        """Deserialize from compressed JSON."""
        if not COMPRESSION_AVAILABLE:
            raise RuntimeError("gzip not available")
        
        # Try to decompress, fall back to plain JSON if not compressed
        try:
            decompressed = gzip.decompress(data)
            return self._loads_json(decompressed)
        except:
            # Not compressed or compression error - try plain JSON
            return self._loads_json(data)
    
    def compare_sizes(self, data: Any) -> dict:
        """
        Compare serialization sizes for different formats.
        
        Args:
            data: Data to compare
            
        Returns:
            Dictionary with format sizes and compression ratios
        """
        results = {}
        
        # JSON
        json_bytes = self._dumps_json(data)
        json_size = len(json_bytes)
        results['json'] = {
            'size': json_size,
            'ratio': 1.0
        }
        
        # MessagePack
        if MSGPACK_AVAILABLE:
            msgpack_bytes = self._dumps_msgpack(data)
            msgpack_size = len(msgpack_bytes)
            results['msgpack'] = {
                'size': msgpack_size,
                'ratio': msgpack_size / json_size,
                'savings': f"{(1 - msgpack_size/json_size) * 100:.1f}%"
            }
        
        # Compressed JSON
        if COMPRESSION_AVAILABLE:
            compressed = gzip.compress(json_bytes)
            compressed_size = len(compressed)
            results['json-gzip'] = {
                'size': compressed_size,
                'ratio': compressed_size / json_size,
                'savings': f"{(1 - compressed_size/json_size) * 100:.1f}%"
            }
        
        return results


def format_bytes(size_bytes: int) -> str:
    """
    Format byte size as human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def benchmark_serialization(data: Any) -> None:
    """
    Benchmark different serialization formats and print results.
    
    Args:
        data: Data to benchmark
    """
    import time
    
    print("\n=== Serialization Benchmark ===\n")
    
    # JSON
    start = time.perf_counter()
    json_bytes = json.dumps(data).encode('utf-8')
    json_time = (time.perf_counter() - start) * 1000
    json_size = len(json_bytes)
    
    print(f"JSON:")
    print(f"  Size: {format_bytes(json_size)}")
    print(f"  Serialize: {json_time:.2f} ms")
    
    start = time.perf_counter()
    _ = json.loads(json_bytes.decode('utf-8'))
    json_load_time = (time.perf_counter() - start) * 1000
    print(f"  Deserialize: {json_load_time:.2f} ms")
    
    # MessagePack
    if MSGPACK_AVAILABLE:
        start = time.perf_counter()
        msgpack_bytes = msgpack.packb(data)
        msgpack_time = (time.perf_counter() - start) * 1000
        msgpack_size = len(msgpack_bytes)
        
        print(f"\nMessagePack:")
        print(f"  Size: {format_bytes(msgpack_size)} ({(1 - msgpack_size/json_size)*100:.1f}% smaller)")
        print(f"  Serialize: {msgpack_time:.2f} ms ({msgpack_time/json_time:.1f}x vs JSON)")
        
        start = time.perf_counter()
        _ = msgpack.unpackb(msgpack_bytes)
        msgpack_load_time = (time.perf_counter() - start) * 1000
        print(f"  Deserialize: {msgpack_load_time:.2f} ms ({msgpack_load_time/json_load_time:.1f}x vs JSON)")
    
    # Compressed JSON
    if COMPRESSION_AVAILABLE:
        start = time.perf_counter()
        compressed = gzip.compress(json_bytes)
        compress_time = (time.perf_counter() - start) * 1000
        compressed_size = len(compressed)
        
        print(f"\nJSON + GZIP:")
        print(f"  Size: {format_bytes(compressed_size)} ({(1 - compressed_size/json_size)*100:.1f}% smaller)")
        print(f"  Compress: {compress_time:.2f} ms")
        
        start = time.perf_counter()
        decompressed = gzip.decompress(compressed)
        decompress_time = (time.perf_counter() - start) * 1000
        print(f"  Decompress: {decompress_time:.2f} ms")
    
    print("\n" + "="*35 + "\n")


# Example usage
if __name__ == "__main__":
    # Example: Compare formats
    sample_data = {
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
            for i in range(100)  # 100 reports
        ]
    }
    
    # Compare sizes
    serializer = Serializer()
    comparison = serializer.compare_sizes(sample_data)
    
    print("\n=== Format Comparison ===")
    for format_name, stats in comparison.items():
        size_mb = stats['size'] / (1024 * 1024)
        print(f"{format_name:12s}: {size_mb:.2f} MB (ratio: {stats['ratio']:.2f})")
        if 'savings' in stats:
            print(f"             Savings: {stats['savings']}")
    
    # Run benchmark
    benchmark_serialization(sample_data)
