"""
Tests for django_lark.templatetags.lark_tags module.
"""

from unittest.mock import MagicMock

import lark
import pytest

from django_lark.templatetags.lark_tags import (
    get_billing_state,
    get_lark_external_id,
    get_subscriptions,
    has_active_subscription,
    has_subscription_to_rate_card,
    lark_subscription_status_badge,
)


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock()
    user.pk = 1
    user.email = "test@example.com"
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_context(mock_user):
    """Create a mock template context with user."""
    return {"user": mock_user}


@pytest.fixture
def mock_context_anonymous():
    """Create a mock template context with anonymous user."""
    user = MagicMock()
    user.is_authenticated = False
    return {"user": user}


class TestHasActiveSubscription:
    """Tests for has_active_subscription template tag."""

    def test_returns_true_with_active_subscription(
        self, mock_context, mock_lark_client
    ):
        """Returns True when user has active subscription."""
        result = has_active_subscription(mock_context)

        assert result is True

    def test_returns_false_without_subscription(self, mock_context, mock_lark_client):
        """Returns False when user has no active subscription."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(has_active_subscription=False)
        )

        result = has_active_subscription(mock_context)

        assert result is False

    def test_returns_false_for_anonymous_user(self, mock_context_anonymous):
        """Returns False for anonymous users."""
        result = has_active_subscription(mock_context_anonymous)
        assert result is False

    def test_accepts_explicit_user(self, mock_user, mock_lark_client):
        """Can pass user explicitly instead of from context."""
        result = has_active_subscription({}, user=mock_user)

        assert result is True


class TestGetBillingState:
    """Tests for get_billing_state template tag."""

    def test_returns_billing_state(self, mock_context, mock_lark_client):
        """Returns billing state for authenticated user."""
        result = get_billing_state(mock_context)

        assert result is not None
        assert result.has_active_subscription is True

    def test_returns_none_for_anonymous_user(self, mock_context_anonymous):
        """Returns None for anonymous users."""
        result = get_billing_state(mock_context_anonymous)
        assert result is None


class TestGetSubscriptions:
    """Tests for get_subscriptions template tag."""

    def test_returns_subscriptions(self, mock_context, mock_lark_client):
        """Returns subscriptions for authenticated user."""
        result = get_subscriptions(mock_context)

        assert len(result) == 2

    def test_returns_empty_for_anonymous_user(self, mock_context_anonymous):
        """Returns empty list for anonymous users."""
        result = get_subscriptions(mock_context_anonymous)
        assert result == []

    def test_raises_on_api_error(self, mock_context, mock_lark_client):
        """Raises APIError when API call fails."""
        mock_request = MagicMock()
        mock_lark_client.subscriptions.list.side_effect = lark.APIError(
            "Error", mock_request, body=None
        )

        with pytest.raises(lark.APIError):
            get_subscriptions(mock_context)


class TestHasSubscriptionToRateCard:
    """Tests for has_subscription_to_rate_card template tag."""

    def test_returns_true_with_matching_rate_card(self, mock_context, mock_lark_client):
        """Returns True when user has subscription to rate card."""
        result = has_subscription_to_rate_card(mock_context, "rc_pro")

        assert result is True

    def test_returns_false_without_matching_rate_card(
        self, mock_context, mock_lark_client
    ):
        """Returns False when user doesn't have subscription to rate card."""
        result = has_subscription_to_rate_card(mock_context, "rc_enterprise")

        assert result is False

    def test_returns_false_for_anonymous_user(self, mock_context_anonymous):
        """Returns False for anonymous users."""
        result = has_subscription_to_rate_card(mock_context_anonymous, "rc_pro")
        assert result is False


class TestGetLarkExternalId:
    """Tests for get_lark_external_id template tag."""

    def test_returns_external_id(self, mock_context):
        """Returns external_id for authenticated user."""
        result = get_lark_external_id(mock_context)
        assert result == "test@example.com"

    def test_returns_none_for_anonymous_user(self, mock_context_anonymous):
        """Returns None for anonymous users."""
        result = get_lark_external_id(mock_context_anonymous)
        assert result is None


class TestLarkSubscriptionStatusBadge:
    """Tests for lark_subscription_status_badge filter."""

    def test_active_status(self):
        """Returns success badge for active status."""
        assert lark_subscription_status_badge("active") == "bg-success"

    def test_cancelled_status(self):
        """Returns danger badge for cancelled status."""
        assert lark_subscription_status_badge("cancelled") == "bg-danger"

    def test_paused_status(self):
        """Returns warning badge for paused status."""
        assert lark_subscription_status_badge("paused") == "bg-warning"

    def test_trialing_status(self):
        """Returns info badge for trialing status."""
        assert lark_subscription_status_badge("trialing") == "bg-info"

    def test_unknown_status(self):
        """Returns secondary badge for unknown status."""
        assert lark_subscription_status_badge("unknown") == "bg-secondary"
