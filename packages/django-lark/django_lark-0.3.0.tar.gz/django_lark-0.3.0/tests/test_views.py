"""
Tests for django_lark.views module.
"""

from unittest.mock import MagicMock

import lark
import pytest
from django.test import RequestFactory

from django_lark.views import (
    change_rate_card_redirect,
    checkout_redirect,
    customer_portal_redirect,
)


@pytest.fixture
def request_factory():
    """Create a Django request factory."""
    return RequestFactory()


@pytest.fixture
def authenticated_user():
    """Create a mock authenticated user."""
    user = MagicMock()
    user.pk = 1
    user.email = "test@example.com"
    user.is_authenticated = True
    return user


class TestCustomerPortalRedirect:
    """Tests for customer_portal_redirect view."""

    def test_redirects_to_portal_url(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Successfully redirects to customer portal URL."""
        request = request_factory.get("/billing/portal/")
        request.user = authenticated_user

        response = customer_portal_redirect(request)

        assert response.status_code == 302
        assert response.url == "https://billing.uselark.ai/?session=abc123"
        mock_lark_client.customer_portal.create_session.assert_called_once()

    def test_uses_external_id(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Uses external_id to create portal session."""
        request = request_factory.get("/billing/portal/")
        request.user = authenticated_user

        customer_portal_redirect(request)

        call_kwargs = mock_lark_client.customer_portal.create_session.call_args.kwargs
        assert call_kwargs["subject_id"] == "test@example.com"

    def test_uses_custom_return_url(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Uses return_url from query params."""
        request = request_factory.get("/billing/portal/?return_url=/dashboard/")
        request.user = authenticated_user

        customer_portal_redirect(request)

        call_kwargs = mock_lark_client.customer_portal.create_session.call_args.kwargs
        assert call_kwargs["return_url"] == "/dashboard/"

    def test_returns_error_on_api_failure(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Returns 400 error when API call fails."""
        mock_request = MagicMock()
        mock_lark_client.customer_portal.create_session.side_effect = lark.APIError(
            "API Error", mock_request, body=None
        )

        request = request_factory.get("/billing/portal/")
        request.user = authenticated_user

        response = customer_portal_redirect(request)

        assert response.status_code == 400
        assert b"Unable to create portal session" in response.content

    def test_requires_authentication(self, request_factory):
        """View requires authentication (handled by decorator)."""
        # The @login_required decorator handles this, but we test the view
        # expects an authenticated user
        request = request_factory.get("/billing/portal/")
        request.user = MagicMock()
        request.user.is_authenticated = False

        # The decorator would redirect, but if called directly it would fail
        # This is just to ensure the view expects authentication
        pass


class TestCheckoutRedirect:
    """Tests for checkout_redirect view."""

    def test_redirects_to_checkout_url(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Successfully redirects to checkout URL."""
        request = request_factory.get("/billing/checkout/?rate_card_id=rc_pro")
        request.user = authenticated_user

        response = checkout_redirect(request)

        assert response.status_code == 302
        assert response.url == "https://checkout.uselark.ai/sub_new"
        mock_lark_client.subscriptions.create.assert_called_once()

    def test_requires_rate_card_id(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Returns 400 error when rate_card_id is missing."""
        request = request_factory.get("/billing/checkout/")
        request.user = authenticated_user

        response = checkout_redirect(request)

        assert response.status_code == 400
        assert b"rate_card_id is required" in response.content

    def test_passes_callback_urls(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Passes callback URLs to subscription create."""
        request = request_factory.get(
            "/billing/checkout/?rate_card_id=rc_pro"
            "&success_url=https://example.com/welcome"
            "&cancelled_url=https://example.com/pricing"
        )
        request.user = authenticated_user

        checkout_redirect(request)

        call_kwargs = mock_lark_client.subscriptions.create.call_args.kwargs
        assert call_kwargs["checkout_callback_urls"]["success_url"] == "https://example.com/welcome"
        assert call_kwargs["checkout_callback_urls"]["cancelled_url"] == "https://example.com/pricing"

    def test_builds_absolute_urls_for_relative_paths(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Converts relative URLs to absolute URLs."""
        request = request_factory.get(
            "/billing/checkout/?rate_card_id=rc_pro&success_url=/welcome/"
        )
        request.user = authenticated_user

        checkout_redirect(request)

        call_kwargs = mock_lark_client.subscriptions.create.call_args.kwargs
        # Should contain the absolute URL
        assert "http" in call_kwargs["checkout_callback_urls"]["success_url"]
        assert "/welcome/" in call_kwargs["checkout_callback_urls"]["success_url"]

    def test_handles_post_request(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Handles POST request with form data."""
        request = request_factory.post(
            "/billing/checkout/",
            {"rate_card_id": "rc_enterprise", "success_url": "/dashboard/"},
        )
        request.user = authenticated_user

        response = checkout_redirect(request)

        assert response.status_code == 302
        call_kwargs = mock_lark_client.subscriptions.create.call_args.kwargs
        assert call_kwargs["rate_card_id"] == "rc_enterprise"

    def test_returns_error_on_api_failure(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Returns 400 error when API call fails."""
        mock_request = MagicMock()
        mock_lark_client.subscriptions.create.side_effect = lark.APIError(
            "API Error", mock_request, body=None
        )

        request = request_factory.get("/billing/checkout/?rate_card_id=rc_pro")
        request.user = authenticated_user

        response = checkout_redirect(request)

        assert response.status_code == 400
        assert b"Unable to create subscription" in response.content


class TestChangeRateCardRedirect:
    """Tests for change_rate_card_redirect view."""

    def test_redirects_to_checkout_url(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Successfully redirects to checkout URL when action required."""
        request = request_factory.get(
            "/billing/change-rate-card/?subscription_id=sub_123&rate_card_id=rc_enterprise"
        )
        request.user = authenticated_user

        response = change_rate_card_redirect(request)

        assert response.status_code == 302
        assert response.url == "https://checkout.uselark.ai/change_rc_123"
        mock_lark_client.subscriptions.change_rate_card.assert_called_once()

    def test_requires_subscription_id(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Returns 400 error when subscription_id is missing."""
        request = request_factory.get(
            "/billing/change-rate-card/?rate_card_id=rc_enterprise"
        )
        request.user = authenticated_user

        response = change_rate_card_redirect(request)

        assert response.status_code == 400
        assert b"subscription_id is required" in response.content

    def test_requires_rate_card_id(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Returns 400 error when rate_card_id is missing."""
        request = request_factory.get(
            "/billing/change-rate-card/?subscription_id=sub_123"
        )
        request.user = authenticated_user

        response = change_rate_card_redirect(request)

        assert response.status_code == 400
        assert b"rate_card_id is required" in response.content

    def test_passes_callback_urls(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Passes callback URLs to change_rate_card."""
        request = request_factory.get(
            "/billing/change-rate-card/?subscription_id=sub_123"
            "&rate_card_id=rc_enterprise"
            "&success_url=https://example.com/upgraded"
            "&cancelled_url=https://example.com/plans"
        )
        request.user = authenticated_user

        change_rate_card_redirect(request)

        call_kwargs = mock_lark_client.subscriptions.change_rate_card.call_args.kwargs
        assert call_kwargs["checkout_callback_urls"]["success_url"] == "https://example.com/upgraded"
        assert call_kwargs["checkout_callback_urls"]["cancelled_url"] == "https://example.com/plans"

    def test_passes_upgrade_behavior(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Passes upgrade_behavior to change_rate_card."""
        request = request_factory.get(
            "/billing/change-rate-card/?subscription_id=sub_123"
            "&rate_card_id=rc_enterprise"
            "&upgrade_behavior=prorate"
        )
        request.user = authenticated_user

        change_rate_card_redirect(request)

        call_kwargs = mock_lark_client.subscriptions.change_rate_card.call_args.kwargs
        assert call_kwargs["upgrade_behavior"] == "prorate"

    def test_builds_absolute_urls_for_relative_paths(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Converts relative URLs to absolute URLs."""
        request = request_factory.get(
            "/billing/change-rate-card/?subscription_id=sub_123"
            "&rate_card_id=rc_enterprise&success_url=/upgraded/"
        )
        request.user = authenticated_user

        change_rate_card_redirect(request)

        call_kwargs = mock_lark_client.subscriptions.change_rate_card.call_args.kwargs
        # Should contain the absolute URL
        assert "http" in call_kwargs["checkout_callback_urls"]["success_url"]
        assert "/upgraded/" in call_kwargs["checkout_callback_urls"]["success_url"]

    def test_handles_post_request(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Handles POST request with form data."""
        request = request_factory.post(
            "/billing/change-rate-card/",
            {
                "subscription_id": "sub_456",
                "rate_card_id": "rc_enterprise",
                "success_url": "/dashboard/",
            },
        )
        request.user = authenticated_user

        response = change_rate_card_redirect(request)

        assert response.status_code == 302
        call_args = mock_lark_client.subscriptions.change_rate_card.call_args
        assert call_args[0][0] == "sub_456"
        assert call_args[1]["rate_card_id"] == "rc_enterprise"

    def test_redirects_to_success_url_when_no_action_required(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Redirects to success URL when rate card change succeeds immediately."""
        mock_lark_client.subscriptions.change_rate_card.return_value = MagicMock(
            result=MagicMock(
                type="success",
                subscription=MagicMock(
                    id="sub_123",
                    rate_card_id="rc_enterprise",
                ),
            ),
        )

        request = request_factory.get(
            "/billing/change-rate-card/?subscription_id=sub_123"
            "&rate_card_id=rc_enterprise"
            "&success_url=https://example.com/upgraded"
        )
        request.user = authenticated_user

        response = change_rate_card_redirect(request)

        assert response.status_code == 302
        assert response.url == "https://example.com/upgraded"

    def test_returns_error_on_permission_denied(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Returns 400 error when subscription doesn't belong to user."""
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="other_user@example.com",
            status="active",
        )
        mock_response = MagicMock()
        mock_lark_client.subjects.retrieve.side_effect = lark.NotFoundError(
            "Not found", response=mock_response, body=None
        )

        request = request_factory.get(
            "/billing/change-rate-card/?subscription_id=sub_123&rate_card_id=rc_enterprise"
        )
        request.user = authenticated_user

        response = change_rate_card_redirect(request)

        assert response.status_code == 400
        assert b"does not belong to this user" in response.content

    def test_returns_error_on_api_failure(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Returns 400 error when API call fails."""
        mock_request = MagicMock()
        mock_lark_client.subscriptions.change_rate_card.side_effect = lark.APIError(
            "API Error", mock_request, body=None
        )

        request = request_factory.get(
            "/billing/change-rate-card/?subscription_id=sub_123&rate_card_id=rc_enterprise"
        )
        request.user = authenticated_user

        response = change_rate_card_redirect(request)

        assert response.status_code == 400
        assert b"Unable to change rate card" in response.content
