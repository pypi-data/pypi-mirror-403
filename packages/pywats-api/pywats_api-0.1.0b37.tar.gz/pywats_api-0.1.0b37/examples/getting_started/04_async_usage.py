"""
Async Usage Examples
====================

pyWATS supports both synchronous and asynchronous usage patterns.
The library uses an async-first architecture where all business logic 
lives in async services, and sync services are thin wrappers.

Run this example:
    python examples/getting_started/04_async_usage.py
"""
import asyncio
import os
from datetime import datetime


# =============================================================================
# Example 1: Synchronous Usage (Default - Simplest)
# =============================================================================

def sync_example():
    """Standard synchronous usage - blocking but simple."""
    from pywats import pyWATS
    
    api = pyWATS(
        base_url=os.environ.get("WATS_BASE_URL", "https://your-server.com"),
        token=os.environ.get("WATS_AUTH_TOKEN", "your-token")
    )
    
    # Synchronous calls - blocks until complete
    print("Fetching products (sync)...")
    products = api.product.get_products()
    print(f"  Found {len(products)} products")
    
    # Each call blocks sequentially
    print("Fetching assets (sync)...")
    assets = api.asset.get_assets(top=5)
    print(f"  Found {len(assets)} assets")
    
    return products, assets


# =============================================================================
# Example 2: Asynchronous Usage (High Performance)
# =============================================================================

async def async_example():
    """Async usage - non-blocking, allows concurrent requests."""
    from pywats import AsyncWATS
    
    # Use async context manager for proper cleanup
    async with AsyncWATS(
        base_url=os.environ.get("WATS_BASE_URL", "https://your-server.com"),
        token=os.environ.get("WATS_AUTH_TOKEN", "your-token")
    ) as api:
        # Single async call
        print("Fetching products (async)...")
        products = await api.product.get_products()
        print(f"  Found {len(products)} products")
        
        # Concurrent requests - much faster!
        print("Fetching products, assets, and version concurrently...")
        start = datetime.now()
        
        products, assets, version = await asyncio.gather(
            api.product.get_products(),
            api.asset.get_assets(top=10),
            api.analytics.get_version()
        )
        
        elapsed = (datetime.now() - start).total_seconds()
        print(f"  Completed 3 requests in {elapsed:.2f}s")
        print(f"  Products: {len(products)}, Assets: {len(assets)}, Version: {version}")
        
        return products, assets, version


# =============================================================================
# Example 3: Using run_sync() for Mixed Code
# =============================================================================

def mixed_example():
    """Call async code from synchronous context using run_sync()."""
    from pywats.core.sync_runner import run_sync
    from pywats import AsyncWATS
    
    async def fetch_all_data():
        """Async function that fetches multiple things."""
        async with AsyncWATS(
            base_url=os.environ.get("WATS_BASE_URL", "https://your-server.com"),
            token=os.environ.get("WATS_AUTH_TOKEN", "your-token")
        ) as api:
            # Use asyncio.gather for concurrent fetching
            return await asyncio.gather(
                api.product.get_products(),
                api.asset.get_assets(top=5)
            )
    
    # Call async from sync using run_sync
    print("Calling async code from sync context...")
    products, assets = run_sync(fetch_all_data())
    print(f"  Got {len(products)} products and {len(assets)} assets")
    
    return products, assets


# =============================================================================
# Example 4: Service Layer Architecture
# =============================================================================

def service_architecture_example():
    """Understanding the sync/async service architecture."""
    
    # All domains have both sync and async services
    from pywats.domains.product.service import ProductService           # Sync
    from pywats.domains.product.async_service import AsyncProductService  # Async
    
    # The sync service is a thin wrapper around the async service
    # Both share the same business logic (in AsyncProductService)
    
    print("Service Architecture:")
    print("  AsyncProductService - Source of truth (all business logic)")
    print("  ProductService      - Thin sync wrapper using run_sync()")
    print()
    print("Available domains:")
    domains = [
        "analytics", "asset", "process", "product", 
        "production", "report", "rootcause", "scim", "software"
    ]
    for domain in domains:
        print(f"  - {domain}/async_service.py (async)")
        print(f"  - {domain}/service.py (sync wrapper)")


# =============================================================================
# Example 5: Async with Error Handling
# =============================================================================

async def async_with_error_handling():
    """Proper error handling in async code."""
    from pywats import AsyncWATS
    from pywats.core.exceptions import (
        AuthenticationError,
        NotFoundError,
        ServerError,
        PyWATSError
    )
    
    try:
        async with AsyncWATS(
            base_url=os.environ.get("WATS_BASE_URL", "https://your-server.com"),
            token=os.environ.get("WATS_AUTH_TOKEN", "your-token")
        ) as api:
            # Try to fetch a product
            product = await api.product.get_product("MAYBE-EXISTS")
            print(f"Found product: {product.part_number}")
            
    except AuthenticationError:
        print("Authentication failed - check your token")
        
    except NotFoundError as e:
        print(f"Product not found: {e}")
        
    except ServerError as e:
        print(f"Server error: {e}")
        
    except PyWATSError as e:
        print(f"API error: {e}")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("pyWATS Async Usage Examples")
    print("=" * 60)
    
    # Check for credentials
    if not os.environ.get("WATS_BASE_URL"):
        print("\n⚠️  Set WATS_BASE_URL and WATS_AUTH_TOKEN environment variables")
        print("   to run the live examples.\n")
        
        # Just show the service architecture (no API needed)
        print("-" * 60)
        service_architecture_example()
    else:
        # Run all examples
        print("\n1. Synchronous Example")
        print("-" * 60)
        sync_example()
        
        print("\n2. Asynchronous Example")
        print("-" * 60)
        asyncio.run(async_example())
        
        print("\n3. Mixed Sync/Async Example")
        print("-" * 60)
        mixed_example()
        
        print("\n4. Service Architecture")
        print("-" * 60)
        service_architecture_example()
        
        print("\n5. Async with Error Handling")
        print("-" * 60)
        asyncio.run(async_with_error_handling())
    
    print("\n" + "=" * 60)
    print("Done!")
