"""
Pytest fixtures for django-lark tests.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from django_lark.client import clear_client_cache


@pytest.fixture(autouse=True)
def lark_settings():
    """Set up Lark settings for all tests."""
    # Clear any cached settings
    from django_lark.conf import clear_settings_cache

    clear_settings_cache()
    clear_client_cache()

    with patch.dict(
        os.environ,
        {
            "LARK_API_KEY": "test_api_key",
            "LARK_BASE_URL": "https://test.api.uselark.ai",
        },
    ):
        yield

    clear_settings_cache()
    clear_client_cache()


@pytest.fixture
def mock_lark_client():
    """Mock Lark client for testing."""
    clear_client_cache()

    with patch("django_lark.client.Lark") as mock_class:
        client = MagicMock()
        mock_class.return_value = client

        # Setup common responses
        client.subjects.list.return_value = MagicMock(
            subjects=[
                MagicMock(
                    id="subj_123", name="Test User", email="test@example.com"
                ),
            ],
            has_more=False,
        )
        client.subjects.retrieve.return_value = MagicMock(
            id="subj_123",
            name="Test User",
            email="test@example.com",
            external_id="user_1",
            metadata={},
            created_at=None,
        )
        client.subjects.create.return_value = MagicMock(
            id="subj_new",
            name="Test User",
            email="test@example.com",
            external_id="test@example.com",
        )
        client.subjects.update.return_value = MagicMock(
            id="subj_123",
            name="Test User",
            email="test@example.com",
        )
        client.customer_access.retrieve_billing_state.return_value = MagicMock(
            has_active_subscription=True,
            active_subscriptions=[
                MagicMock(rate_card_id="rc_pro", subscription_id="sub_123"),
            ],
        )
        client.customer_portal.create_session.return_value = MagicMock(
            url="https://billing.uselark.ai/?session=abc123"
        )
        client.subscriptions.list.return_value = MagicMock(
            subscriptions=[MagicMock(id="sub_1"), MagicMock(id="sub_2")],
            has_more=False,
        )
        client.subscriptions.create.return_value = MagicMock(
            result=MagicMock(
                result_type="requires_action",
                action=MagicMock(
                    checkout_url="https://checkout.uselark.ai/sub_new",
                    requires_action_type="checkout",
                ),
            ),
        )
        client.subscriptions.cancel.return_value = MagicMock(
            id="sub_123",
            rate_card_id="rc_pro",
            subject_id="test@example.com",
            status="cancelled",
        )
        client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            rate_card_id="rc_pro",
            subject_id="test@example.com",
            status="active",
        )
        client.subscriptions.change_rate_card.return_value = MagicMock(
            result=MagicMock(
                type="requires_action",
                action=MagicMock(
                    checkout_url="https://checkout.uselark.ai/change_rc_123",
                    type="checkout",
                ),
            ),
        )
        client.usage_events.create.return_value = MagicMock(
            id="evt_123",
            event_name="api_calls",
            subject_id="test@example.com",
        )

        yield client

    clear_client_cache()


@pytest.fixture
def mock_async_lark_client():
    """Mock AsyncLark client for testing."""
    clear_client_cache()

    with patch("django_lark.client.AsyncLark") as mock_class:
        client = MagicMock()
        mock_class.return_value = client
        yield client

    clear_client_cache()
