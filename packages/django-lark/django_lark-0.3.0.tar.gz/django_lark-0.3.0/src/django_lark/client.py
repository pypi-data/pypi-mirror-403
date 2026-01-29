"""
Lark client factory functions with optional caching.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Optional

from lark import AsyncLark, Lark

from .conf import get_settings

if TYPE_CHECKING:
    from .conf import LarkSettings


# Thread-safe client cache
_client_lock = threading.Lock()
_sync_client: Optional[Lark] = None
_async_client: Optional[AsyncLark] = None


def get_lark_client(
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: Optional[float] = None,
    max_retries: Optional[int] = None,
    use_cache: Optional[bool] = None,
) -> Lark:
    """
    Get a synchronous Lark client instance.

    If caching is enabled (default) and no overrides are provided,
    returns a cached singleton instance.

    Args:
        api_key: Override API key from settings.
        base_url: Override base URL from settings.
        timeout: Override timeout from settings.
        max_retries: Override max retries from settings.
        use_cache: Override cache setting. If True and overrides provided,
                   a new client is created but not cached.

    Returns:
        Lark: Configured synchronous client instance.

    Example:
        # Use default settings
        client = get_lark_client()
        subjects = client.subjects.list()

        # Override for specific call
        client = get_lark_client(timeout=120, use_cache=False)
    """
    global _sync_client

    settings = get_settings()

    # Determine if we should use cache
    should_cache = use_cache if use_cache is not None else settings.client_cache_enabled
    has_overrides = any([api_key, base_url, timeout is not None, max_retries is not None])

    # If using cache and no overrides, return cached client
    if should_cache and not has_overrides:
        if _sync_client is None:
            with _client_lock:
                if _sync_client is None:
                    _sync_client = _create_sync_client(settings)
        return _sync_client

    # Create new client with overrides
    return _create_sync_client(
        settings,
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
    )


def get_async_lark_client(
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: Optional[float] = None,
    max_retries: Optional[int] = None,
    use_cache: Optional[bool] = None,
) -> AsyncLark:
    """
    Get an asynchronous Lark client instance.

    If caching is enabled (default) and no overrides are provided,
    returns a cached singleton instance.

    Args:
        api_key: Override API key from settings.
        base_url: Override base URL from settings.
        timeout: Override timeout from settings.
        max_retries: Override max retries from settings.
        use_cache: Override cache setting.

    Returns:
        AsyncLark: Configured asynchronous client instance.

    Example:
        async def view(request):
            client = get_async_lark_client()
            subjects = await client.subjects.list()
    """
    global _async_client

    settings = get_settings()

    should_cache = use_cache if use_cache is not None else settings.client_cache_enabled
    has_overrides = any([api_key, base_url, timeout is not None, max_retries is not None])

    if should_cache and not has_overrides:
        if _async_client is None:
            with _client_lock:
                if _async_client is None:
                    _async_client = _create_async_client(settings)
        return _async_client

    return _create_async_client(
        settings,
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
    )


def _create_sync_client(
    settings: LarkSettings,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: Optional[float] = None,
    max_retries: Optional[int] = None,
) -> Lark:
    """Create a new synchronous client instance."""
    return Lark(
        api_key=api_key or settings.api_key,
        base_url=base_url or settings.base_url,
        timeout=timeout if timeout is not None else settings.timeout,
        max_retries=max_retries if max_retries is not None else settings.max_retries,
    )


def _create_async_client(
    settings: LarkSettings,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: Optional[float] = None,
    max_retries: Optional[int] = None,
) -> AsyncLark:
    """Create a new asynchronous client instance."""
    return AsyncLark(
        api_key=api_key or settings.api_key,
        base_url=base_url or settings.base_url,
        timeout=timeout if timeout is not None else settings.timeout,
        max_retries=max_retries if max_retries is not None else settings.max_retries,
    )


def clear_client_cache() -> None:
    """
    Clear cached client instances.

    Useful for testing or when settings change.
    """
    global _sync_client, _async_client
    with _client_lock:
        _sync_client = None
        _async_client = None
