import asyncio
import hashlib
import inspect
import json
import os
import logging
from functools import wraps
from typing import Any, Callable, List, Optional, Union
import threading

import diskcache as dc

# Setup a logger for the DCache module.
# Users can configure this logger's handlers and level in their application.
logger = logging.getLogger(__name__)
if not logger.hasHandlers(): # Add a default NullHandler to prevent "No handler found" warnings
    logger.addHandler(logging.NullHandler())



class DCache:
    """
    A flexible caching class using diskcache, designed for caching results of functions,
    especially I/O-bound or computationally intensive operations like LLM calls.
    It supports both synchronous and asynchronous functions.
    """
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        n_async_read_semaphore: int = 20,
        n_async_write_semaphore: int = 10,
        n_sync_read_semaphore: int = 20,
        n_sync_write_semaphore: int = 10,
        diskcache_shards: int = 64,
        diskcache_timeout: float = 5.0,  # Timeout for diskcache SQLite operations
        default_ttl: Optional[float] = None, # Default Time-To-Live for cache entries in seconds
    ):
        """
        Initialize the DCache instance.

        Parameters:
            cache_dir (Optional[str]): Path to the cache directory. Defaults to ".dcache"
                                     in the current working directory.
            n_async_read_semaphore (int): Max concurrent asyncio-based cache reads.
            n_async_write_semaphore (int): Max concurrent asyncio-based cache writes.
            n_sync_read_semaphore (int): Max concurrent thread-based cache reads.
            n_sync_write_semaphore (int): Max concurrent thread-based cache writes.
            diskcache_shards (int): Number of shards for diskcache.FanoutCache.
            diskcache_timeout (float): Timeout in seconds for diskcache operations.
            default_ttl (Optional[float]): Default expiration time for cache entries in seconds.
                                           Can be overridden per decorated function.
        """
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), ".dcache")
        os.makedirs(self.cache_dir, exist_ok=True)

        self.cache = dc.FanoutCache(
            self.cache_dir,
            shards=diskcache_shards,
            timeout=diskcache_timeout,
        )
        self.default_ttl = default_ttl

        self.async_read_semaphore = asyncio.Semaphore(n_async_read_semaphore)
        self.async_write_semaphore = asyncio.Semaphore(n_async_write_semaphore)
        self.sync_read_semaphore = threading.Semaphore(n_sync_read_semaphore)
        self.sync_write_semaphore = threading.Semaphore(n_sync_write_semaphore)

        # Sentinel object to differentiate a cache miss from a cached value of None
        self._sentinel = object()

        logger.info(
            f"DCache initialized. Directory: {self.cache_dir}, "
            f"Async Semaphores (R/W): {n_async_read_semaphore}/{n_async_write_semaphore}, "
            f"Sync Semaphores (R/W): {n_sync_read_semaphore}/{n_sync_write_semaphore}, "
            f"DiskCache Timeout: {diskcache_timeout}s, Default TTL: {default_ttl}s"
        )

    def _serialize_value(self, value: Any) -> Any:
        """Attempts to JSON dump, falls back to string representation for key generation."""
        if hasattr(value, 'to_dict'):
            value = value.to_dict()
        try:
            json.dumps(value) # Test serializability for JSON
            return value
        except (TypeError, OverflowError):
            return str(value) # Fallback to string

    def _generate_cache_key(self, function: Callable, args: tuple, kwargs: dict,
                            param_names: List[str], exclude_args_list: List[str]) -> str:
        """
        Generates a cache key based on the function's identity and serialized arguments.
        """
        serialized_args = []
        if args: # Only process args if there are any
            for i, arg_val in enumerate(args):
                # Exclude positional arguments by name if specified
                if param_names and i < len(param_names) and param_names[i] in exclude_args_list:
                    continue
                serialized_args.append(self._serialize_value(arg_val))

        serialized_kwargs = {}
        if kwargs: # Only process kwargs if there are any
            for k, v in kwargs.items():
                # Exclude keyword arguments by name
                if k in exclude_args_list:
                    continue
                serialized_kwargs[k] = self._serialize_value(v)
        
        key_payload = {
            "module": function.__module__,
            "name": function.__qualname__,
            "args": serialized_args,
            "kwargs": sorted(serialized_kwargs.items()), # Sort kwargs by key for consistency
        }
        # Using ensure_ascii=False for better Unicode handling, encoding to utf-8
        serialized_payload = json.dumps(key_payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized_payload.encode('utf-8')).hexdigest()

    def __call__(self, possible_func: Optional[Callable] = None, *,
                 required_kwargs: Optional[List[str]] = None,
                 exclude_args: Optional[List[str]] = None,
                 ttl: Optional[float] = None,
                 serializer: Optional[Callable[[Any], Any]] = None,
                 deserializer: Optional[Callable[[Any], Any]] = None):
        """
        Decorator for caching function results.

        Can be used as `@dcache` or `@dcache(required_kwargs=[...], exclude_args=[...], ttl=...)`.

        Args:
            possible_func: The function to be decorated (if used as `@dcache`).
            required_kwargs: List of keyword argument names that *must* be present
                             for caching to be attempted.
            exclude_args: List of argument names (positional or keyword) to exclude
                          from cache key generation (e.g., "self", "cls").
            ttl: Time-to-live for this specific function's cache entries in seconds.
                 Overrides the instance's `default_ttl`.
            serializer: Optional function to transform the result before caching.
                        Signature: (result) -> serializable_result
            deserializer: Optional function to transform cached data after retrieval.
                          Signature: (cached_data) -> result
        """
        actual_required_kwargs = required_kwargs or []
        actual_exclude_args = exclude_args or []
        # If ttl is explicitly set to None in decorator, it means no expiration for this func,
        # otherwise use decorator ttl, else instance default_ttl.
        actual_ttl = ttl if ttl is not None else self.default_ttl

        def decorator_builder(func: Callable):
            is_async = inspect.iscoroutinefunction(func)
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            func_qualname = func.__qualname__ # For logging

            if is_async:
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    if actual_required_kwargs and not all(k in kwargs for k in actual_required_kwargs):
                        logger.debug(f"Cache bypass for {func_qualname}: missing required_kwargs.")
                        return await func(*args, **kwargs)

                    key = self._generate_cache_key(func, args, kwargs, param_names, actual_exclude_args)
                    
                    # 1. Try to read from cache
                    if not kwargs.pop('_cache_overwrite', False):
                        try:
                            async with self.async_read_semaphore:
                                cached_value = await asyncio.to_thread(
                                    self.cache.get, key, default=self._sentinel
                                )
                            if cached_value is not self._sentinel:
                                logger.info(f"Async cache hit: {func_qualname} (key: {key[:8]}...).")
                                # Apply deserializer if provided
                                if deserializer is not None:
                                    cached_value = deserializer(cached_value)
                                return cached_value
                        except Exception as e:
                            logger.error(f"Async cache read error: {func_qualname} (key: {key[:8]}...): {e}", exc_info=True)
                            # Fall through to recompute if read fails

                    logger.info(f"Async cache miss: {func_qualname} (key: {key[:8]}...).")

                    # 2. Compute result
                    result = await func(*args, **kwargs)

                    # 3. Try to write to cache
                    try:
                        # Apply serializer if provided
                        cache_value = serializer(result) if serializer is not None else result
                        async with self.async_write_semaphore:
                            await asyncio.to_thread(self.cache.set, key, cache_value, expire=actual_ttl)
                        logger.info(f"Async cache set: {func_qualname} (key: {key[:8]}...). TTL: {actual_ttl}s")
                    except Exception as e:
                        logger.error(f"Async cache write error: {func_qualname} (key: {key[:8]}...): {e}", exc_info=True)
                        # Value is computed, just caching failed. Do not re-raise by default.

                    return result
                return async_wrapper
            else: # Synchronous function
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    if actual_required_kwargs and not all(k in kwargs for k in actual_required_kwargs):
                        logger.debug(f"Cache bypass for {func_qualname}: missing required_kwargs.")
                        return func(*args, **kwargs)

                    key = self._generate_cache_key(func, args, kwargs, param_names, actual_exclude_args)

                    # 1. Try to read from cache
                    if not kwargs.pop('_cache_overwrite', False):
                        try:
                            with self.sync_read_semaphore:
                                cached_value = self.cache.get(key, default=self._sentinel)
                            if cached_value is not self._sentinel:
                                logger.info(f"Sync cache hit: {func_qualname} (key: {key[:8]}...).")
                                # Apply deserializer if provided
                                if deserializer is not None:
                                    cached_value = deserializer(cached_value)
                                return cached_value
                        except Exception as e:
                            logger.error(f"Sync cache read error: {func_qualname} (key: {key[:8]}...): {e}", exc_info=True)

                    logger.info(f"Sync cache miss: {func_qualname} (key: {key[:8]}...).")

                    # 2. Compute result
                    result = func(*args, **kwargs)

                    # 3. Try to write to cache
                    try:
                        # Apply serializer if provided
                        cache_value = serializer(result) if serializer is not None else result
                        with self.sync_write_semaphore:
                            self.cache.set(key, cache_value, expire=actual_ttl)
                        logger.info(f"Sync cache set: {func_qualname} (key: {key[:8]}...). TTL: {actual_ttl}s")
                    except Exception as e:
                        logger.error(f"Sync cache write error: {func_qualname} (key: {key[:8]}...): {e}", exc_info=True)
                    return result
                return sync_wrapper
        if callable(possible_func):
            # Used as @dcache
            return decorator_builder(possible_func)
        else:
            # Used as @dcache(...)
            return decorator_builder

    # --- Manual Cache Interaction Methods ---
    def get(self, key: str, default: Any = None) -> Any:
        """Manually get an item from the cache (synchronous)."""
        try:
            with self.sync_read_semaphore:
                cached_value = self.cache.get(key, default=self._sentinel)
            return default if cached_value is self._sentinel else cached_value
        except Exception as e:
            logger.error(f"Manual cache get error (key: {key[:8]}): {e}", exc_info=True)
            return default

    def set(self, key: str, value: Any, expire: Optional[float] = None) -> None:
        """Manually set an item in the cache (synchronous)."""
        actual_expire = expire if expire is not None else self.default_ttl
        try:
            with self.sync_write_semaphore:
                self.cache.set(key, value, expire=actual_expire)
            logger.info(f"Manual cache set (key: {key[:8]}...). TTL: {actual_expire}s")
        except Exception as e:
            logger.error(f"Manual cache set error (key: {key[:8]}): {e}", exc_info=True)

    def delete(self, key: str) -> bool:
        """Manually delete an item from the cache (synchronous). Returns True if key was deleted."""
        try:
            with self.sync_write_semaphore: # Uses write semaphore for deletion
                # FanoutCache.delete returns the number of shards the key was deleted from.
                # We'll simplify to True if any deletions occurred (or if it simply ran).
                # To be more precise, one might check if key existed before.
                # For now, assume diskcache.delete is idempotent / doesn't error on missing key.
                self.cache.delete(key) # diskcache.delete returns count, not bool
            logger.info(f"Manual cache delete attempted (key: {key[:8]}...).")
            return True # Simplified, actual deletion success depends on diskcache internals
        except Exception as e:
            logger.error(f"Manual cache delete error (key: {key[:8]}): {e}", exc_info=True)
            return False

    def clear(self) -> bool:
        """Clear all items from the cache (synchronous). Returns True on success."""
        try:
            with self.sync_write_semaphore: # Protect with a semaphore
                self.cache.clear()
            logger.info("Cache cleared.")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}", exc_info=True)
            return False

    def close(self) -> None:
        """Close the cache and release resources."""
        try:
            self.cache.close()
            logger.info("DCache connection closed.")
        except Exception as e:
            logger.error(f"Error closing DCache: {e}", exc_info=True)


def dcache(*args, **kwargs):
    cache = DCache()
    if len(args) > 0:
        func = args[0]
        return cache(func, **kwargs)
    else:
        def _dcache(func):
            return cache(func, **kwargs)
        return _dcache