"""
Tests for django_lark.client module.
"""

from unittest.mock import MagicMock, patch

import pytest

from django_lark.client import (
    clear_client_cache,
    get_async_lark_client,
    get_lark_client,
)


class TestGetLarkClient:
    """Tests for get_lark_client function."""

    def test_returns_lark_client(self, mock_lark_client):
        """Returns a Lark client instance."""
        client = get_lark_client()
        assert client is not None

    def test_caches_client_by_default(self):
        """Caches client by default."""
        clear_client_cache()

        with patch("django_lark.client.Lark") as mock_lark:
            mock_lark.return_value = MagicMock()

            client1 = get_lark_client()
            client2 = get_lark_client()

            # Should only create one client
            assert mock_lark.call_count == 1
            assert client1 is client2

        clear_client_cache()

    def test_creates_new_client_with_overrides(self):
        """Creates new client when overrides are provided."""
        clear_client_cache()

        with patch("django_lark.client.Lark") as mock_lark:
            # Return different mocks each time
            mock_lark.side_effect = [MagicMock(name="client1"), MagicMock(name="client2")]

            client1 = get_lark_client()
            client2 = get_lark_client(timeout=120)

            # Should create two clients
            assert mock_lark.call_count == 2
            # They should be different objects
            assert client1 is not client2

        clear_client_cache()

    def test_uses_settings_for_config(self):
        """Uses settings for client configuration."""
        clear_client_cache()

        with patch("django_lark.client.Lark") as mock_lark:
            mock_lark.return_value = MagicMock()

            get_lark_client()

            call_kwargs = mock_lark.call_args.kwargs
            assert call_kwargs["api_key"] == "test_api_key"
            assert call_kwargs["base_url"] == "https://test.api.uselark.ai"

        clear_client_cache()

    def test_can_disable_cache(self):
        """Can disable caching."""
        clear_client_cache()

        with patch("django_lark.client.Lark") as mock_lark:
            mock_lark.side_effect = [MagicMock(name="client1"), MagicMock(name="client2")]

            client1 = get_lark_client(use_cache=False)
            client2 = get_lark_client(use_cache=False)

            # Should create two clients
            assert mock_lark.call_count == 2

        clear_client_cache()


class TestGetAsyncLarkClient:
    """Tests for get_async_lark_client function."""

    def test_returns_async_client(self, mock_async_lark_client):
        """Returns an AsyncLark client instance."""
        client = get_async_lark_client()
        assert client is not None

    def test_caches_async_client(self):
        """Caches async client by default."""
        clear_client_cache()

        with patch("django_lark.client.AsyncLark") as mock_lark:
            mock_lark.return_value = MagicMock()

            client1 = get_async_lark_client()
            client2 = get_async_lark_client()

            assert mock_lark.call_count == 1
            assert client1 is client2

        clear_client_cache()


class TestClearClientCache:
    """Tests for clear_client_cache function."""

    def test_clears_cached_clients(self):
        """Clears both sync and async cached clients."""
        with patch("django_lark.client.Lark") as mock_lark:
            with patch("django_lark.client.AsyncLark") as mock_async:
                mock_lark.return_value = MagicMock()
                mock_async.return_value = MagicMock()

                # Create cached clients
                get_lark_client()
                get_async_lark_client()

                # Clear cache
                clear_client_cache()

                # Create new clients
                get_lark_client()
                get_async_lark_client()

                # Should have created 2 of each
                assert mock_lark.call_count == 2
                assert mock_async.call_count == 2

        clear_client_cache()
