"""
Async API Runner - Composition-based async API helper for GUI pages

Provides clean integration between Qt GUI and AsyncWATS via dependency injection.
Replaces the mixin pattern with explicit composition for better testability.

Usage:
    # In MainWindow:
    runner = AsyncAPIRunner(facade)
    page = MyPage(config, async_api_runner=runner)
    
    # In page:
    def _on_refresh(self):
        self.async_api.run(
            lambda api: api.asset.get_assets(),
            on_success=self._on_assets_loaded,
            on_error=self._on_error,
            task_name="Loading assets..."
        )
"""

from __future__ import annotations

import asyncio
import logging
import weakref
from typing import (
    Any, Awaitable, Callable, Optional, TypeVar, Union, TYPE_CHECKING
)

if TYPE_CHECKING:
    from pywats import pyWATS, AsyncWATS
    from .pages.base import BasePage

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncAPIRunner:
    """
    Helper for running API calls from GUI pages using composition.
    
    Features:
    - Auto-detect sync vs async API
    - Unified interface for API calls
    - Automatic async-to-sync bridging via AsyncTaskRunner
    - Error handling with loading states
    - Memory-safe weak references to pages
    
    This class is injected into pages that need async API access.
    It requires the page to have:
    - run_async() method (from BasePage)
    - handle_error() method (from ErrorHandlingMixin)
    """
    
    def __init__(self, facade: Any) -> None:
        """
        Initialize runner with service facade.
        
        Args:
            facade: Service facade providing API access
        """
        self._facade = facade
        self._pages: list[weakref.ref] = []  # Track pages for cleanup
    
    def register_page(self, page: 'BasePage') -> None:
        """
        Register a page for cleanup tracking.
        
        Args:
            page: Page to register
        """
        self._pages.append(weakref.ref(page))
    
    @property
    def has_api(self) -> bool:
        """Check if API is available"""
        return bool(self._facade and self._facade.has_api)
    
    @property
    def has_async_api(self) -> bool:
        """Check if async API is available"""
        if not self._facade:
            return False
        return hasattr(self._facade, 'async_api') and self._facade.async_api is not None
    
    def get_sync_api(self) -> Optional['pyWATS']:
        """
        Get sync API client (pyWATS).
        
        Returns:
            pyWATS instance or None
        """
        if self._facade and self._facade.has_api:
            return self._facade.api
        return None
    
    def get_async_api_sync(self) -> Optional['AsyncWATS']:
        """
        Get async API client (AsyncWATS) - sync access.
        
        Returns:
            AsyncWATS instance or None
        """
        if self._facade and hasattr(self._facade, 'async_api'):
            return self._facade.async_api
        return None
    
    async def get_async_api(self) -> 'AsyncWATS':
        """
        Get async API client (AsyncWATS) - for use in async context.
        
        Raises:
            RuntimeError: If async API not available
        """
        api = self.get_async_api_sync()
        if api is None:
            raise RuntimeError("Async API not available. Ensure service is connected.")
        return api
    
    def run(
        self,
        page: 'BasePage',
        api_call: Union[Callable[['pyWATS'], T], Callable[['AsyncWATS'], Awaitable[T]]],
        on_success: Optional[Callable[[T], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        task_name: str = "Loading...",
        show_loading: bool = True
    ) -> Optional[str]:
        """
        Run an API call with automatic sync/async handling.
        
        This is the main method pages use to make API calls.
        It will:
        1. Use async API if available (non-blocking)
        2. Fall back to sync API in thread if async not available
        3. Show loading indicator
        4. Handle errors gracefully
        
        Args:
            page: Page making the call (needs run_async and handle_error methods)
            api_call: Function that takes API client and returns result.
                     Can be sync (for pyWATS) or async (for AsyncWATS)
            on_success: Callback with result on success
            on_error: Callback with exception on error
            task_name: Name shown in loading indicator
            show_loading: Whether to show loading indicator
        
        Returns:
            Task ID (can be used to cancel) or None if sync
        
        Example:
            self.async_api.run(
                self,
                lambda api: api.asset.get_assets(),
                on_success=self._on_assets_loaded
            )
        """
        if not self.has_api:
            error = RuntimeError("Not connected to WATS server")
            if on_error:
                on_error(error)
            return None
        
        # Validate page has required methods
        self._validate_page(page)
        
        # Prefer async API
        if self.has_async_api:
            return self._run_async_api_call(
                page, api_call, on_success, on_error, task_name, show_loading
            )
        else:
            # Fall back to sync API in thread
            return self._run_sync_api_call(
                page, api_call, on_success, on_error, task_name, show_loading
            )
    
    def _validate_page(self, page: 'BasePage') -> None:
        """
        Validate that page has required methods.
        
        Args:
            page: Page to validate
        
        Raises:
            TypeError: If required methods are missing
        """
        missing = []
        if not hasattr(page, 'run_async') or not callable(getattr(page, 'run_async', None)):
            missing.append('run_async')
        if not hasattr(page, 'handle_error') or not callable(getattr(page, 'handle_error', None)):
            missing.append('handle_error')
        
        if missing:
            raise TypeError(
                f"{page.__class__.__name__} must have {', '.join(missing)} method(s)"
            )
    
    def _run_async_api_call(
        self,
        page: 'BasePage',
        api_call: Callable[['AsyncWATS'], Awaitable[T]],
        on_success: Optional[Callable[[T], None]],
        on_error: Optional[Callable[[Exception], None]],
        task_name: str,
        show_loading: bool
    ) -> str:
        """Run API call using async API"""
        api = self.get_async_api_sync()
        
        async def _execute():
            return await api_call(api)
        
        from ..core.async_runner import TaskResult
        
        def _on_complete(result: TaskResult):
            if result.is_success and on_success:
                on_success(result.result)
            elif result.is_error and on_error:
                on_error(result.error)
            elif result.is_error:
                page.handle_error(result.error, task_name)
        
        return page.run_async(
            _execute(),
            name=task_name,
            on_complete=_on_complete,
            show_loading=show_loading
        )
    
    def _run_sync_api_call(
        self,
        page: 'BasePage',
        api_call: Callable[['pyWATS'], T],
        on_success: Optional[Callable[[T], None]],
        on_error: Optional[Callable[[Exception], None]],
        task_name: str,
        show_loading: bool
    ) -> str:
        """Run sync API call in thread"""
        api = self.get_sync_api()
        
        async def _execute():
            # Run sync call in thread pool
            return await asyncio.to_thread(api_call, api)
        
        from ..core.async_runner import TaskResult
        
        def _on_complete(result: TaskResult):
            if result.is_success and on_success:
                on_success(result.result)
            elif result.is_error and on_error:
                on_error(result.error)
            elif result.is_error:
                page.handle_error(result.error, task_name)
        
        return page.run_async(
            _execute(),
            name=task_name,
            on_complete=_on_complete,
            show_loading=show_loading
        )
    
    def require_api(
        self, 
        page: 'BasePage',
        action: str = "perform this action"
    ) -> bool:
        """
        Check if API is available, show message if not.
        
        Args:
            page: Page requesting API
            action: Description of what user is trying to do
        
        Returns:
            True if API is available, False otherwise
        """
        if not self.has_api:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                page,
                "Not Connected",
                f"Please connect to WATS server to {action}."
            )
            return False
        return True
    
    def run_parallel(
        self,
        page: 'BasePage',
        *calls: tuple[Callable, str],
        on_all_complete: Optional[Callable[[list], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """
        Run multiple API calls in PARALLEL (all start at once).
        
        Use this when calls are independent and can run concurrently.
        Results are returned in the same order as the calls.
        
        Args:
            page: Page making the calls
            *calls: Tuples of (api_call, task_name)
            on_all_complete: Called when all complete with list of results
            on_error: Called if any fails
        
        Example:
            self.async_api.run_parallel(
                self,
                (lambda api: api.asset.get_types(), "Loading types..."),
                (lambda api: api.asset.get_assets(), "Loading assets..."),
                on_all_complete=self._on_data_loaded
            )
        """
        results = [None] * len(calls)  # Pre-allocate to preserve order
        completed = [0]  # Use list to allow mutation in closure
        
        def make_success_handler(idx, total):
            def handler(result):
                results[idx] = result
                completed[0] += 1
                if completed[0] == total and on_all_complete:
                    on_all_complete(results)
            return handler
        
        for idx, (call, name) in enumerate(calls):
            self.run(
                page,
                call,
                on_success=make_success_handler(idx, len(calls)),
                on_error=on_error,
                task_name=name
            )
    
    def run_sequence(
        self,
        page: 'BasePage',
        *calls: tuple[Callable, str],
        on_all_complete: Optional[Callable[[list], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """
        Run multiple API calls in SEQUENCE (one after another).
        
        Use this when later calls depend on earlier results,
        or when you need guaranteed ordering.
        
        Args:
            page: Page making the calls
            *calls: Tuples of (api_call, task_name)
            on_all_complete: Called when all complete with list of results
            on_error: Called if any fails (stops the sequence)
        
        Example:
            self.async_api.run_sequence(
                self,
                (lambda api: api.product.get_products(), "Loading products..."),
                (lambda api: api.product.get_bom(self._selected_product), "Loading BOM..."),
                on_all_complete=self._on_data_loaded
            )
        """
        if not calls:
            if on_all_complete:
                on_all_complete([])
            return
        
        results = []
        calls_list = list(calls)  # Convert to list for indexing
        
        def run_next(idx: int):
            if idx >= len(calls_list):
                # All done
                if on_all_complete:
                    on_all_complete(results)
                return
            
            call, name = calls_list[idx]
            
            def on_success(result):
                results.append(result)
                # Run next call
                run_next(idx + 1)
            
            def on_err(e):
                if on_error:
                    on_error(e)
                # Stop sequence on error (don't run remaining calls)
            
            self.run(
                page,
                call,
                on_success=on_success,
                on_error=on_err,
                task_name=name
            )
        
        # Start the sequence
        run_next(0)
