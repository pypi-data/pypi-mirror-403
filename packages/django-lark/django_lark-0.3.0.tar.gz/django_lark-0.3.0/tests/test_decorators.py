"""
Tests for django_lark.decorators module.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import lark
import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from django_lark.decorators import subscription_required, track_usage, usage_within_limits


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


@pytest.fixture
def unauthenticated_user():
    """Create a mock unauthenticated user."""
    user = MagicMock()
    user.is_authenticated = False
    return user


class TestSubscriptionRequired:
    """Tests for subscription_required decorator."""

    def test_allows_access_with_active_subscription(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Allows access when user has active subscription."""

        @subscription_required()
        def protected_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/protected/")
        request.user = authenticated_user

        response = protected_view(request)

        assert response.status_code == 200
        assert response.content == b"Success"

    def test_denies_access_without_subscription(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Denies access when user has no active subscription."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=False,
                active_subscriptions=[],
            )
        )

        @subscription_required()
        def protected_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/protected/")
        request.user = authenticated_user

        response = protected_view(request)

        assert response.status_code == 403
        assert b"Active subscription required" in response.content

    def test_denies_access_to_unauthenticated_user(
        self, request_factory, unauthenticated_user
    ):
        """Denies access to unauthenticated users."""

        @subscription_required()
        def protected_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/protected/")
        request.user = unauthenticated_user

        response = protected_view(request)

        assert response.status_code == 403
        assert b"Authentication required" in response.content

    def test_redirects_unauthenticated_user_with_redirect_url(
        self, request_factory, unauthenticated_user
    ):
        """Redirects unauthenticated user when redirect_url is set."""

        @subscription_required(redirect_url="/login/")
        def protected_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/protected/")
        request.user = unauthenticated_user

        response = protected_view(request)

        assert response.status_code == 302
        assert "/login/" in response.url

    def test_redirects_without_subscription_with_redirect_url(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Redirects user without subscription when redirect_url is set."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=False,
                active_subscriptions=[],
            )
        )

        @subscription_required(redirect_url="/pricing/")
        def protected_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/protected/")
        request.user = authenticated_user

        response = protected_view(request)

        assert response.status_code == 302
        assert "/pricing/" in response.url

    def test_checks_specific_rate_cards(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Allows access only with specific rate cards."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=True,
                active_subscriptions=[
                    MagicMock(rate_card_id="rc_pro"),
                ],
            )
        )

        @subscription_required(rate_card_ids=["rc_pro", "rc_enterprise"])
        def protected_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/protected/")
        request.user = authenticated_user

        response = protected_view(request)

        assert response.status_code == 200

    def test_denies_without_required_rate_card(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Denies access when user doesn't have required rate card."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=True,
                active_subscriptions=[
                    MagicMock(rate_card_id="rc_basic"),
                ],
            )
        )

        @subscription_required(rate_card_ids=["rc_pro", "rc_enterprise"])
        def protected_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/protected/")
        request.user = authenticated_user

        response = protected_view(request)

        assert response.status_code == 403
        assert b"Required subscription tier not found" in response.content

    def test_handles_api_error(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Handles API errors gracefully."""
        mock_request = MagicMock()
        mock_lark_client.customer_access.retrieve_billing_state.side_effect = (
            lark.APIError("API Error", mock_request, body=None)
        )

        @subscription_required()
        def protected_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/protected/")
        request.user = authenticated_user

        response = protected_view(request)

        assert response.status_code == 403
        assert b"Unable to verify subscription" in response.content

    def test_uses_external_id_for_lookup(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Uses external_id to look up billing state."""

        @subscription_required()
        def protected_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/protected/")
        request.user = authenticated_user

        protected_view(request)

        mock_lark_client.customer_access.retrieve_billing_state.assert_called_once_with(
            "test@example.com"
        )


class TestTrackUsage:
    """Tests for track_usage decorator."""

    def test_tracks_usage_on_successful_response(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Records usage event when view returns 200."""

        @track_usage("api_calls")
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/")
        request.user = authenticated_user

        response = api_view(request)

        assert response.status_code == 200
        mock_lark_client.usage_events.create.assert_called_once()
        call_kwargs = mock_lark_client.usage_events.create.call_args.kwargs
        assert call_kwargs["event_name"] == "api_calls"
        assert call_kwargs["subject_id"] == "test@example.com"
        assert call_kwargs["data"] == {}
        assert call_kwargs["timestamp"] is not None

    def test_uses_custom_data(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Uses custom data dict when provided."""

        @track_usage("api_calls", data={"count": 5, "endpoint": "users"})
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/")
        request.user = authenticated_user

        api_view(request)

        call_kwargs = mock_lark_client.usage_events.create.call_args.kwargs
        assert call_kwargs["data"] == {"count": 5, "endpoint": "users"}

    def test_uses_callable_data(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Uses callable to generate data."""

        def get_data(request, response, *args, **kwargs):
            return {"path": request.path, "count": 1}

        @track_usage("api_calls", data=get_data)
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/users/")
        request.user = authenticated_user

        api_view(request)

        call_kwargs = mock_lark_client.usage_events.create.call_args.kwargs
        assert call_kwargs["data"] == {"path": "/api/users/", "count": 1}

    def test_uses_callable_timestamp(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Uses callable to generate timestamp."""
        now = datetime.now(timezone.utc)

        def get_timestamp(request, response, *args, **kwargs):
            return now

        @track_usage("api_calls", timestamp=get_timestamp)
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/users/")
        request.user = authenticated_user

        api_view(request)

        call_kwargs = mock_lark_client.usage_events.create.call_args.kwargs
        assert call_kwargs["timestamp"] == now

    def test_uses_callable_idempotency_key(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Uses callable to generate idempotency key."""

        def get_key(request, response, *args, **kwargs):
            return f"request_{request.path}"

        @track_usage("api_calls", idempotency_key=get_key)
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/users/")
        request.user = authenticated_user

        api_view(request)

        call_kwargs = mock_lark_client.usage_events.create.call_args.kwargs
        assert call_kwargs["idempotency_key"] == "request_/api/users/"

    def test_does_not_track_on_error_response(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Does not record usage on 4xx/5xx responses."""

        @track_usage("api_calls")
        def api_view(request):
            return HttpResponse("Not Found", status=404)

        request = request_factory.get("/api/")
        request.user = authenticated_user

        response = api_view(request)

        assert response.status_code == 404
        mock_lark_client.usage_events.create.assert_not_called()

    def test_tracks_custom_success_codes(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Tracks usage for custom success codes."""

        @track_usage("api_calls", success_codes=[200, 201, 202])
        def api_view(request):
            return HttpResponse("Created", status=201)

        request = request_factory.get("/api/")
        request.user = authenticated_user

        response = api_view(request)

        assert response.status_code == 201
        mock_lark_client.usage_events.create.assert_called_once()

    def test_does_not_track_for_unauthenticated_user(
        self, request_factory, unauthenticated_user, mock_lark_client
    ):
        """Does not record usage for unauthenticated users."""

        @track_usage("api_calls")
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/")
        request.user = unauthenticated_user

        response = api_view(request)

        assert response.status_code == 200
        mock_lark_client.usage_events.create.assert_not_called()

    def test_fails_silently_on_api_error(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Continues normally if usage recording fails."""
        mock_request = MagicMock()
        mock_lark_client.usage_events.create.side_effect = lark.APIError(
            "API Error", mock_request, body=None
        )

        @track_usage("api_calls")
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/")
        request.user = authenticated_user

        response = api_view(request)

        # View should still return successfully
        assert response.status_code == 200
        assert response.content == b"Success"

    def test_generates_uuid_idempotency_key_by_default(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Generates UUID idempotency key when not provided."""

        @track_usage("api_calls")
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/")
        request.user = authenticated_user

        api_view(request)

        call_kwargs = mock_lark_client.usage_events.create.call_args.kwargs
        # Should be a valid UUID format
        key = call_kwargs["idempotency_key"]
        assert len(key) == 36  # UUID format: 8-4-4-4-12
        assert key.count("-") == 4


class TestDecoratorsComposed:
    """Tests for using decorators together."""

    def test_subscription_required_and_track_usage_together(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Both decorators work together - subscription check then usage tracking."""

        @subscription_required()
        @track_usage("premium_api_calls")
        def premium_api(request):
            return HttpResponse("Premium content")

        request = request_factory.get("/api/premium/")
        request.user = authenticated_user

        response = premium_api(request)

        # View should succeed
        assert response.status_code == 200
        assert response.content == b"Premium content"

        # Usage should be tracked
        mock_lark_client.usage_events.create.assert_called_once()
        call_kwargs = mock_lark_client.usage_events.create.call_args.kwargs
        assert call_kwargs["event_name"] == "premium_api_calls"
        assert call_kwargs["subject_id"] == "test@example.com"

    def test_subscription_required_blocks_before_track_usage(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Subscription check blocks access before usage is tracked."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=False,
                active_subscriptions=[],
            )
        )

        @subscription_required()
        @track_usage("premium_api_calls")
        def premium_api(request):
            return HttpResponse("Premium content")

        request = request_factory.get("/api/premium/")
        request.user = authenticated_user

        response = premium_api(request)

        # View should be blocked
        assert response.status_code == 403

        # Usage should NOT be tracked (subscription check failed)
        mock_lark_client.usage_events.create.assert_not_called()

    def test_track_usage_with_subscription_required_rate_cards(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Track usage works with rate card restrictions."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=True,
                active_subscriptions=[
                    MagicMock(rate_card_id="rc_enterprise"),
                ],
            )
        )

        @subscription_required(rate_card_ids=["rc_pro", "rc_enterprise"])
        @track_usage("enterprise_api_calls", data={"tier": "enterprise"})
        def enterprise_api(request):
            return HttpResponse("Enterprise content")

        request = request_factory.get("/api/enterprise/")
        request.user = authenticated_user

        response = enterprise_api(request)

        # View should succeed
        assert response.status_code == 200

        # Usage should be tracked with custom data
        call_kwargs = mock_lark_client.usage_events.create.call_args.kwargs
        assert call_kwargs["event_name"] == "enterprise_api_calls"
        assert call_kwargs["data"] == {"tier": "enterprise"}


class TestUsageWithinLimits:
    """Tests for usage_within_limits decorator."""

    def test_allows_access_when_within_limits(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Allows access when user is within usage limits."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=True,
                has_overage_for_usage=False,
                usage_data=[],
            )
        )

        @usage_within_limits()
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/")
        request.user = authenticated_user

        response = api_view(request)

        assert response.status_code == 200
        assert response.content == b"Success"

    def test_denies_access_when_over_limits(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Denies access when user has exceeded usage limits."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=True,
                has_overage_for_usage=True,
                usage_data=[
                    MagicMock(
                        rate_name="API Calls",
                        included_units=1000,
                        used_units="1500",
                    )
                ],
            )
        )

        @usage_within_limits()
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/")
        request.user = authenticated_user

        response = api_view(request)

        assert response.status_code == 403
        assert b"Usage limit exceeded" in response.content

    def test_redirects_when_over_limits_with_redirect_url(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Redirects to upgrade page when over limits."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=True,
                has_overage_for_usage=True,
                usage_data=[],
            )
        )

        @usage_within_limits(redirect_url="/upgrade/")
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/")
        request.user = authenticated_user

        response = api_view(request)

        assert response.status_code == 302
        assert "/upgrade/" in response.url

    def test_denies_access_to_unauthenticated_user(
        self, request_factory, unauthenticated_user
    ):
        """Denies access to unauthenticated users."""

        @usage_within_limits()
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/")
        request.user = unauthenticated_user

        response = api_view(request)

        assert response.status_code == 403
        assert b"Authentication required" in response.content

    def test_handles_api_error(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Handles API errors gracefully."""
        mock_request = MagicMock()
        mock_lark_client.customer_access.retrieve_billing_state.side_effect = (
            lark.APIError("API Error", mock_request, body=None)
        )

        @usage_within_limits()
        def api_view(request):
            return HttpResponse("Success")

        request = request_factory.get("/api/")
        request.user = authenticated_user

        response = api_view(request)

        assert response.status_code == 403
        assert b"Unable to verify usage limits" in response.content

    def test_combines_with_subscription_required(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Works correctly with subscription_required decorator."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=True,
                has_overage_for_usage=False,
                active_subscriptions=[
                    MagicMock(rate_card_id="rc_pro"),
                ],
                usage_data=[],
            )
        )

        @subscription_required()
        @usage_within_limits()
        def premium_api(request):
            return HttpResponse("Premium content")

        request = request_factory.get("/api/premium/")
        request.user = authenticated_user

        response = premium_api(request)

        assert response.status_code == 200
        assert response.content == b"Premium content"

    def test_subscription_required_blocks_before_usage_check(
        self, request_factory, authenticated_user, mock_lark_client
    ):
        """Subscription check runs first before usage limit check."""
        mock_lark_client.customer_access.retrieve_billing_state.return_value = (
            MagicMock(
                has_active_subscription=False,
                has_overage_for_usage=True,  # Would fail if reached
                active_subscriptions=[],
                usage_data=[],
            )
        )

        @subscription_required()
        @usage_within_limits()
        def premium_api(request):
            return HttpResponse("Premium content")

        request = request_factory.get("/api/premium/")
        request.user = authenticated_user

        response = premium_api(request)

        # Should fail on subscription check, not usage check
        assert response.status_code == 403
        assert b"Active subscription required" in response.content
