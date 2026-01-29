import asyncio
import builtins
import functools
import inspect
import random
import sys
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])

# Sentinel value to distinguish between None and missing cache entries
_MISSING = object()

# Cleanup probability (1 in N chance to run cleanup on set)
_CLEANUP_PROBABILITY = 0.05


@dataclass
class CacheEntry:
    """Cache entry with value and metadata."""

    value: Any
    timestamp: float
    access_count: int = 0
    # Cached size estimate (computed lazily)
    _cached_size: Optional[int] = field(default=None, repr=False)

    def is_expired(self, ttl: Optional[float]) -> bool:
        """Check if entry is expired based on TTL."""
        if ttl is None:
            return False
        return time.time() - self.timestamp > ttl


@dataclass
class CacheStats:
    """Cache statistics."""

    current_size: int
    max_size: int
    ttl: Optional[float]
    hits: int
    misses: int
    total_size_in_memory_bytes: int
    total_size_in_memory_pretty: str


class AsyncLRUCache:
    """Async LRU Cache implementation with optimized performance."""

    def __init__(
        self,
        maxsize: int = 1024,
        ttl: Optional[float] = None,
        ignore_params: Optional[list[str]] = None,
    ) -> None:
        self.maxsize = maxsize
        self.ttl = ttl
        self.ignore_params: frozenset[str] = frozenset(ignore_params or [])
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = asyncio.Lock()
        # Track ongoing computations to prevent duplicate work
        self._pending: dict[str, asyncio.Future[Any]] = {}
        # Counter for probabilistic cleanup
        self._ops_since_cleanup = 0

    def _make_hashable(self, obj: Any) -> Any:
        """Convert unhashable types to hashable equivalents."""
        if isinstance(obj, (str, int, float, bool, type(None), bytes)):
            return obj
        elif isinstance(obj, tuple):
            return tuple(self._make_hashable(item) for item in obj)
        elif isinstance(obj, list):
            return ("__list__", tuple(self._make_hashable(item) for item in obj))
        elif isinstance(obj, dict):
            # Use tuple of sorted items for deterministic hashing
            return (
                "__dict__",
                tuple(sorted((k, self._make_hashable(v)) for k, v in obj.items())),
            )
        elif isinstance(obj, set):
            return ("__set__", tuple(sorted(self._make_hashable(item) for item in obj)))
        elif isinstance(obj, frozenset):
            return (
                "__frozenset__",
                tuple(sorted(self._make_hashable(item) for item in obj)),
            )
        else:
            # For complex objects (dataclasses, pydantic, etc)
            # Check if it's already hashable
            try:
                hash(obj)
                return obj
            except TypeError:
                pass

            # Try __dict__ for dataclasses/pydantic models
            if hasattr(obj, "__dict__"):
                obj_dict: dict[str, Any] = obj.__dict__
                return (obj.__class__.__qualname__, self._make_hashable(obj_dict))

            # Try __slots__
            if hasattr(obj, "__slots__"):
                slots: tuple[str, ...] = obj.__slots__
                slot_values = tuple((slot, self._make_hashable(getattr(obj, slot, None))) for slot in slots if hasattr(obj, slot))
                return (obj.__class__.__qualname__, slot_values)

            # Last resort: use repr
            return repr(obj)

    def _get_cache_key_with_signature(
        self,
        func_module: str,
        func_qualname: str,
        sig: inspect.Signature,
        param_names: tuple[str, ...],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> str:
        """Generate cache key from function arguments using pre-cached signature."""
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Build hashable key components using pre-sorted parameter names
        key_parts: list[Any] = [func_module, func_qualname]

        arguments = bound_args.arguments
        ignore = self.ignore_params

        # Use pre-computed sorted param names to avoid sorting on every call
        for name in param_names:
            if name not in ignore and name in arguments:
                value = arguments[name]
                hashable_value = self._make_hashable(value)
                key_parts.append((name, hashable_value))

        # Use Python's hash directly (fast path)
        try:
            return f"alru:{hash(tuple(key_parts))}"
        except TypeError:
            # Fallback for unhashable types that slipped through
            key_str = repr(key_parts)
            return f"alru:{len(key_str)}:{hash(key_str)}"

    def _format_bytes(self, bytes_size: int) -> str:
        """Format bytes into human-readable string."""
        size: float = float(bytes_size)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    async def get(self, key: str) -> Any:
        """Get value from cache. Returns _MISSING if not found."""
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if entry.is_expired(self.ttl):
                    del self.cache[key]
                    self.misses += 1
                    return _MISSING

                # Move to end (most recently used)
                self.cache.move_to_end(key)
                entry.access_count += 1
                self.hits += 1
                return entry.value

            self.misses += 1
            return _MISSING

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache with optimized cleanup."""
        async with self._lock:
            # Probabilistic cleanup - only run occasionally to avoid O(n) on every insert
            self._ops_since_cleanup += 1
            if self.ttl is not None and (self._ops_since_cleanup >= 100 or random.random() < _CLEANUP_PROBABILITY):
                self._cleanup_expired_unlocked()
                self._ops_since_cleanup = 0

            # If at capacity, remove least recently used
            while len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)

            # Add new entry
            entry = CacheEntry(value=value, timestamp=time.time())
            self.cache[key] = entry

    def _cleanup_expired_unlocked(self) -> None:
        """Remove expired entries from cache. Must be called with lock held."""
        if self.ttl is None:
            return

        current_time = time.time()
        ttl = self.ttl

        # Collect expired keys
        expired_keys = [key for key, entry in self.cache.items() if current_time - entry.timestamp > ttl]

        for key in expired_keys:
            del self.cache[key]

    def _estimate_size_fast(
        self,
        obj: Any,
        depth: int = 0,
        seen: Optional[builtins.set[int]] = None,
    ) -> int:
        """
        Estimate size of an object with depth limiting for performance.

        Uses sampling for large collections to avoid O(n) traversal.
        """
        if depth > 5:  # Limit recursion depth
            return sys.getsizeof(obj)

        if seen is None:
            seen = set()

        obj_id = id(obj)
        if obj_id in seen:
            return 0

        seen.add(obj_id)
        size = sys.getsizeof(obj)

        if isinstance(obj, dict):
            # For large dicts, sample instead of iterating all
            items = list(obj.items())
            if len(items) > 20:
                # Sample ~20 items and extrapolate
                sample = items[:10] + items[-10:]
                sample_size = sum(self._estimate_size_fast(k, depth + 1, seen) + self._estimate_size_fast(v, depth + 1, seen) for k, v in sample)
                size += int(sample_size * len(items) / len(sample))
            else:
                size += sum(self._estimate_size_fast(k, depth + 1, seen) + self._estimate_size_fast(v, depth + 1, seen) for k, v in items)
        elif isinstance(obj, (list, tuple, set, frozenset)):
            items_list: list[Any] = list(obj) if isinstance(obj, (set, frozenset)) else list(obj)
            if len(items_list) > 20:
                # Sample for large collections
                sample_list = items_list[:10] + items_list[-10:]
                sample_size = sum(self._estimate_size_fast(item, depth + 1, seen) for item in sample_list)
                size += int(sample_size * len(items_list) / len(sample_list))
            else:
                size += sum(self._estimate_size_fast(item, depth + 1, seen) for item in items_list)
        elif hasattr(obj, "__dict__"):
            obj_dict: dict[str, Any] = obj.__dict__
            size += self._estimate_size_fast(obj_dict, depth + 1, seen)
        elif hasattr(obj, "__slots__"):
            slots: tuple[str, ...] = obj.__slots__
            size += sum(self._estimate_size_fast(getattr(obj, slot, None), depth + 1, seen) for slot in slots if hasattr(obj, slot))

        return size

    async def get_cache_stats(self) -> CacheStats:
        """Get cache statistics with optimized memory estimation."""
        async with self._lock:
            # Clean up expired entries first
            self._cleanup_expired_unlocked()

            cache_len = len(self.cache)

            if cache_len == 0:
                total_bytes = sys.getsizeof(self.cache) + sys.getsizeof(self._pending)
            else:
                # Sample-based estimation for large caches
                base_overhead = sys.getsizeof(self.cache) + sys.getsizeof(
                    self._pending,
                )

                if cache_len <= 50:
                    # Small cache: measure all entries
                    entry_bytes = 0
                    for key, entry in self.cache.items():
                        entry_bytes += sys.getsizeof(key)
                        entry_bytes += sys.getsizeof(entry)
                        entry_bytes += self._estimate_size_fast(entry.value)
                    total_bytes = base_overhead + entry_bytes
                else:
                    # Large cache: sample and extrapolate
                    cache_items = list(self.cache.items())
                    # Sample from beginning, middle, and end
                    sample_indices = list(range(min(10, cache_len))) + list(range(cache_len // 2 - 5, cache_len // 2 + 5)) + list(range(max(0, cache_len - 10), cache_len))
                    sample_indices = list(
                        {i for i in sample_indices if 0 <= i < cache_len},
                    )

                    sample_bytes = 0
                    for idx in sample_indices:
                        key, entry = cache_items[idx]
                        sample_bytes += sys.getsizeof(key)
                        sample_bytes += sys.getsizeof(entry)
                        sample_bytes += self._estimate_size_fast(entry.value)

                    avg_entry_size = sample_bytes / len(sample_indices)
                    total_bytes = base_overhead + int(avg_entry_size * cache_len)

            return CacheStats(
                current_size=cache_len,
                max_size=self.maxsize,
                ttl=self.ttl,
                hits=self.hits,
                misses=self.misses,
                total_size_in_memory_bytes=total_bytes,
                total_size_in_memory_pretty=self._format_bytes(total_bytes),
            )

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            self._ops_since_cleanup = 0

    async def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry by key."""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    async def invalidate_by_func_args(
        self,
        func_module: str,
        func_qualname: str,
        sig: inspect.Signature,
        param_names: tuple[str, ...],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> bool:
        """Invalidate cache entry by function arguments."""
        key = self._get_cache_key_with_signature(
            func_module,
            func_qualname,
            sig,
            param_names,
            args,
            kwargs,
        )
        return await self.invalidate(key)


class AsyncLRUCacheWrapper:
    """Wrapper that provides the cached function with additional methods."""

    def __init__(self, func: F, cache: AsyncLRUCache) -> None:
        self._func = func
        self._cache = cache
        # Cache the signature and sorted parameter names once
        self._signature = inspect.signature(func)
        self._param_names: tuple[str, ...] = tuple(
            sorted(self._signature.parameters.keys()),
        )
        # Cache module and qualname for key generation
        self._func_module: str = func.__module__
        self._func_qualname: str = func.__qualname__
        functools.update_wrapper(self, func)

    def _get_cache_key(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
        """Generate cache key using cached signature."""
        return self._cache._get_cache_key_with_signature(
            self._func_module,
            self._func_qualname,
            self._signature,
            self._param_names,
            args,
            kwargs,
        )

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the cached function with proper deduplication for concurrent calls."""
        cache_key = self._get_cache_key(args, kwargs)
        cache = self._cache

        # Fast path: check cache without pending logic
        cached_result = await cache.get(cache_key)
        if cached_result is not _MISSING:
            return cached_result

        # Check for pending computation
        pending_future: Optional[asyncio.Future[Any]] = None
        async with cache._lock:
            # Double-check cache after acquiring lock
            if cache_key in cache.cache:
                entry = cache.cache[cache_key]
                if not entry.is_expired(cache.ttl):
                    cache.cache.move_to_end(cache_key)
                    entry.access_count += 1
                    cache.hits += 1
                    return entry.value

            # Check if computation is already in progress
            pending_future = cache._pending.get(cache_key)

        # Wait for pending computation outside the lock
        if pending_future is not None:
            try:
                return await asyncio.shield(pending_future)
            except asyncio.CancelledError:
                raise
            except Exception:
                # If pending computation failed, we'll retry below
                pass

        # Start our own computation
        loop = asyncio.get_event_loop()
        future: asyncio.Future[Any] = loop.create_future()

        # Prevent "Future exception was never retrieved" warning
        def _silence_exception(fut: asyncio.Future[Any]) -> None:
            if fut.done() and not fut.cancelled():
                fut.exception()  # Mark exception as retrieved

        future.add_done_callback(_silence_exception)
        is_owner = False

        async with cache._lock:
            # Final check before starting computation
            if cache_key in cache.cache:
                entry = cache.cache[cache_key]
                if not entry.is_expired(cache.ttl):
                    cache.cache.move_to_end(cache_key)
                    entry.access_count += 1
                    cache.hits += 1
                    return entry.value

            if cache_key not in cache._pending:
                cache._pending[cache_key] = future
                is_owner = True
            else:
                # Someone else started computation, wait for them
                pending_future = cache._pending[cache_key]

        # If we're not the owner, wait for the owner's result
        if not is_owner and pending_future is not None:
            try:
                return await asyncio.shield(pending_future)
            except asyncio.CancelledError:
                raise
            except Exception:
                raise

        # We are the owner, compute the result
        try:
            result = await self._func(*args, **kwargs)
            await cache.set(cache_key, result)
            if not future.done():
                future.set_result(result)
            return result
        except Exception as e:
            if not future.done():
                future.set_exception(e)
            raise
        finally:
            async with cache._lock:
                cache._pending.pop(cache_key, None)

    async def get_cache_stats(self) -> CacheStats:
        """Get cache statistics."""
        return await self._cache.get_cache_stats()

    async def clear_cache(self) -> None:
        """Clear the cache."""
        await self._cache.clear()

    async def cache_invalidate(self, *args: Any, **kwargs: Any) -> bool:
        """
        Invalidate cache entry for specific function arguments.

        Args:
            *args, **kwargs: Same arguments as the original function

        Returns:
            bool: True if entry was found and invalidated, False otherwise
        """
        return await self._cache.invalidate_by_func_args(
            self._func_module,
            self._func_qualname,
            self._signature,
            self._param_names,
            args,
            kwargs,
        )

    def cache_info(self) -> dict[str, Any]:
        """Get cache info (sync version for compatibility)."""
        return {
            "maxsize": self._cache.maxsize,
            "ttl": self._cache.ttl,
            "ignore_params": list(self._cache.ignore_params),
        }

    # Preserve original function attributes
    def __getattr__(self, name: str) -> Any:
        return getattr(self._func, name)


def alru_cache(
    maxsize: int = 1024,
    ttl: Optional[float] = None,
    ignore_params: Optional[list[str]] = None,
) -> Callable[[F], AsyncLRUCacheWrapper]:
    """
    Async LRU Cache decorator.

    Args:
        maxsize: Maximum number of entries in cache (default: 1024)
        ttl: Time to live in seconds (default: None - no expiration)
        ignore_params: List of parameter names to ignore when generating cache keys

    Returns:
        Decorated function with caching capabilities
    """

    def decorator(func: F) -> AsyncLRUCacheWrapper:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("alru_cache can only be applied to async functions")

        cache = AsyncLRUCache(maxsize=maxsize, ttl=ttl, ignore_params=ignore_params)
        wrapper = AsyncLRUCacheWrapper(func, cache)

        return wrapper

    return decorator
