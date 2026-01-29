"""
Tests for django_lark.utils module.
"""

from unittest.mock import MagicMock, patch

import lark
import pytest

from django_lark.utils import (
    acancel_subscription,
    acancel_subscription_for_user,
    achange_subscription_rate_card,
    achange_subscription_rate_card_for_user,
    acreate_subscription_for_user,
    aget_billing_state_for_user,
    aget_or_create_subject_for_user,
    aget_subscriptions_for_user,
    arecord_usage,
    arecord_usage_for_user,
    cancel_subscription,
    cancel_subscription_for_user,
    change_subscription_rate_card,
    change_subscription_rate_card_for_user,
    create_subscription_for_user,
    get_billing_state_for_user,
    get_external_id_for_user,
    get_or_create_subject_for_user,
    get_subscriptions_for_user,
    record_usage,
    record_usage_for_user,
)


@pytest.fixture
def mock_user():
    """Create a mock Django user."""
    user = MagicMock()
    user.pk = 1
    user.email = "test@example.com"
    user.get_full_name.return_value = "Test User"
    user.is_authenticated = True
    return user


class TestGetExternalIdForUser:
    """Tests for get_external_id_for_user function."""

    def test_returns_email_by_default(self, mock_user):
        """Default setting uses email as external_id."""
        external_id = get_external_id_for_user(mock_user)
        assert external_id == "test@example.com"

    def test_returns_django_user_prefix_for_id_field(self, mock_user):
        """When field is 'id', returns 'django_user_{pk}'."""
        with patch("django_lark.utils.get_settings") as mock_settings:
            mock_settings.return_value.user_subject_field = "id"
            external_id = get_external_id_for_user(mock_user)
            assert external_id == "django_user_1"

    def test_returns_custom_field(self, mock_user):
        """Can use any user field as external_id."""
        mock_user.uuid = "abc-123-def"
        with patch("django_lark.utils.get_settings") as mock_settings:
            mock_settings.return_value.user_subject_field = "uuid"
            external_id = get_external_id_for_user(mock_user)
            assert external_id == "abc-123-def"

    def test_callable_field(self, mock_user):
        """Can use a callable to compute external_id."""
        with patch("django_lark.utils.get_settings") as mock_settings:
            mock_settings.return_value.user_subject_field = lambda u: f"custom_{u.pk}"
            external_id = get_external_id_for_user(mock_user)
            assert external_id == "custom_1"


class TestGetOrCreateSubjectForUser:
    """Tests for get_or_create_subject_for_user function."""

    def test_returns_existing_subject(self, mock_user, mock_lark_client):
        """Returns existing subject when found by external_id."""
        subject, created = get_or_create_subject_for_user(mock_user)

        assert subject.id == "subj_123"
        assert created is False
        mock_lark_client.subjects.retrieve.assert_called_once_with("test@example.com")

    def test_creates_subject_when_not_found(self, mock_user, mock_lark_client):
        """Creates new subject when not found and create_if_missing=True."""
        mock_response = MagicMock()
        mock_lark_client.subjects.retrieve.side_effect = lark.NotFoundError(
            "Not found", response=mock_response, body=None
        )

        subject, created = get_or_create_subject_for_user(mock_user)

        assert subject.id == "subj_new"
        assert created is True
        mock_lark_client.subjects.create.assert_called_once_with(
            name="Test User",
            email="test@example.com",
            external_id="test@example.com",
        )

    def test_raises_when_not_found_and_create_disabled(self, mock_user, mock_lark_client):
        """Raises LookupError when subject not found and create_if_missing=False."""
        mock_response = MagicMock()
        mock_lark_client.subjects.retrieve.side_effect = lark.NotFoundError(
            "Not found", response=mock_response, body=None
        )

        with pytest.raises(LookupError):
            get_or_create_subject_for_user(mock_user, create_if_missing=False)

    def test_updates_subject_when_update_if_exists(self, mock_user, mock_lark_client):
        """Updates subject when update_if_exists=True."""
        subject, created = get_or_create_subject_for_user(
            mock_user, update_if_exists=True
        )

        assert created is False
        mock_lark_client.subjects.update.assert_called_once_with(
            "test@example.com",
            name="Test User",
            email="test@example.com",
        )


class TestGetBillingStateForUser:
    """Tests for get_billing_state_for_user function."""

    def test_returns_billing_state(self, mock_user, mock_lark_client):
        """Returns billing state from Lark API."""
        billing_state = get_billing_state_for_user(mock_user)

        assert billing_state.has_active_subscription is True
        mock_lark_client.customer_access.retrieve_billing_state.assert_called_once_with(
            "test@example.com"
        )

    def test_raises_on_api_error(self, mock_user, mock_lark_client):
        """Raises APIError when API call fails."""
        mock_request = MagicMock()
        mock_lark_client.customer_access.retrieve_billing_state.side_effect = (
            lark.APIError("Error", mock_request, body=None)
        )

        with pytest.raises(lark.APIError):
            get_billing_state_for_user(mock_user)


class TestGetSubscriptionsForUser:
    """Tests for get_subscriptions_for_user function."""

    def test_returns_subscriptions(self, mock_user, mock_lark_client):
        """Returns subscriptions from Lark API."""
        result = get_subscriptions_for_user(mock_user)

        mock_lark_client.subscriptions.list.assert_called_once_with(
            subject_id="test@example.com"
        )
        assert len(result.subscriptions) == 2


class TestCreateSubscriptionForUser:
    """Tests for create_subscription_for_user function."""

    def test_creates_subscription(self, mock_user, mock_lark_client):
        """Creates subscription with rate card and returns response."""
        result = create_subscription_for_user(mock_user, rate_card_id="rc_pro")

        mock_lark_client.subscriptions.create.assert_called_once_with(
            rate_card_id="rc_pro",
            subject_id="test@example.com",
        )
        assert result.result.result_type == "requires_action"
        assert result.result.action.checkout_url == "https://checkout.uselark.ai/sub_new"

    def test_creates_subscription_with_callback_urls(self, mock_user, mock_lark_client):
        """Creates subscription with callback URLs."""
        create_subscription_for_user(
            mock_user,
            rate_card_id="rc_pro",
            success_url="https://example.com/success",
            cancelled_url="https://example.com/cancelled",
        )

        call_kwargs = mock_lark_client.subscriptions.create.call_args.kwargs
        assert call_kwargs["checkout_callback_urls"] == {
            "success_url": "https://example.com/success",
            "cancelled_url": "https://example.com/cancelled",
        }

    def test_creates_subscription_with_metadata(self, mock_user, mock_lark_client):
        """Creates subscription with metadata."""
        create_subscription_for_user(
            mock_user,
            rate_card_id="rc_pro",
            metadata={"campaign": "summer_sale"},
        )

        call_kwargs = mock_lark_client.subscriptions.create.call_args.kwargs
        assert call_kwargs["metadata"] == {"campaign": "summer_sale"}

    def test_creates_subscription_with_fixed_rate_quantities(self, mock_user, mock_lark_client):
        """Creates subscription with fixed rate quantities."""
        fixed_quantities = {"seats": 5, "storage_gb": 100}
        create_subscription_for_user(
            mock_user,
            rate_card_id="rc_pro",
            fixed_rate_quantities=fixed_quantities,
        )

        call_kwargs = mock_lark_client.subscriptions.create.call_args.kwargs
        assert call_kwargs["fixed_rate_quantities"] == fixed_quantities

    def test_creates_subscription_with_rate_price_multipliers(self, mock_user, mock_lark_client):
        """Creates subscription with rate price multipliers (discounts)."""
        create_subscription_for_user(
            mock_user,
            rate_card_id="rc_pro",
            rate_price_multipliers={"seats": 0.8},  # 20% discount
        )

        call_kwargs = mock_lark_client.subscriptions.create.call_args.kwargs
        assert call_kwargs["rate_price_multipliers"] == {"seats": 0.8}

    def test_creates_subscription_with_create_checkout_session(self, mock_user, mock_lark_client):
        """Creates subscription with create_checkout_session option."""
        create_subscription_for_user(
            mock_user,
            rate_card_id="rc_pro",
            create_checkout_session="always",
        )

        call_kwargs = mock_lark_client.subscriptions.create.call_args.kwargs
        assert call_kwargs["create_checkout_session"] == "always"


    def test_raises_on_api_error(self, mock_user, mock_lark_client):
        """Raises APIError when API call fails."""
        mock_request = MagicMock()
        mock_lark_client.subscriptions.create.side_effect = lark.APIError(
            "Error", mock_request, body=None
        )

        with pytest.raises(lark.APIError):
            create_subscription_for_user(mock_user, rate_card_id="rc_pro")


class TestCancelSubscription:
    """Tests for cancel_subscription function."""

    def test_cancels_subscription(self, mock_lark_client):
        """Cancels subscription by ID."""
        result = cancel_subscription("sub_123")

        mock_lark_client.subscriptions.cancel.assert_called_once_with("sub_123")
        assert result.status == "cancelled"


class TestCancelSubscriptionForUser:
    """Tests for cancel_subscription_for_user function."""

    def test_cancels_subscription_owned_by_user(self, mock_user, mock_lark_client):
        """Cancels subscription when it belongs to user."""
        # Set up subscription to be owned by user's external_id
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="test@example.com",
            status="active",
        )

        result = cancel_subscription_for_user(mock_user, "sub_123")

        mock_lark_client.subscriptions.cancel.assert_called_once_with("sub_123")
        assert result.status == "cancelled"

    def test_cancels_subscription_with_subject_id_match(self, mock_user, mock_lark_client):
        """Cancels subscription when subject_id matches resolved subject."""
        # Subscription has internal subject_id, not external_id
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="subj_123",
            status="active",
        )
        mock_lark_client.subjects.retrieve.return_value = MagicMock(
            id="subj_123",
            external_id="test@example.com",
        )

        result = cancel_subscription_for_user(mock_user, "sub_123")

        mock_lark_client.subscriptions.cancel.assert_called_once_with("sub_123")
        assert result.status == "cancelled"

    def test_raises_permission_error_for_wrong_user(self, mock_user, mock_lark_client):
        """Raises PermissionError when subscription belongs to another user."""
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="other_user@example.com",
            status="active",
        )
        mock_response = MagicMock()
        mock_lark_client.subjects.retrieve.side_effect = lark.NotFoundError(
            "Not found", response=mock_response, body=None
        )

        with pytest.raises(PermissionError, match="does not belong to this user"):
            cancel_subscription_for_user(mock_user, "sub_123")

    def test_raises_permission_error_when_subject_mismatch(self, mock_user, mock_lark_client):
        """Raises PermissionError when subject lookup shows different owner."""
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="subj_other",
            status="active",
        )
        mock_lark_client.subjects.retrieve.return_value = MagicMock(
            id="subj_123",  # Different from subscription's subject_id
            external_id="test@example.com",
        )

        with pytest.raises(PermissionError, match="does not belong to this user"):
            cancel_subscription_for_user(mock_user, "sub_123")


class TestChangeSubscriptionRateCard:
    """Tests for change_subscription_rate_card function."""

    def test_changes_rate_card(self, mock_lark_client):
        """Changes rate card for a subscription."""
        result = change_subscription_rate_card("sub_123", rate_card_id="rc_enterprise")

        mock_lark_client.subscriptions.change_rate_card.assert_called_once_with(
            "sub_123",
            rate_card_id="rc_enterprise",
        )
        assert result.result.type == "requires_action"
        assert result.result.action.checkout_url == "https://checkout.uselark.ai/change_rc_123"

    def test_changes_rate_card_with_callback_urls(self, mock_lark_client):
        """Changes rate card with callback URLs."""
        change_subscription_rate_card(
            "sub_123",
            rate_card_id="rc_enterprise",
            success_url="https://example.com/success",
            cancelled_url="https://example.com/cancelled",
        )

        call_kwargs = mock_lark_client.subscriptions.change_rate_card.call_args.kwargs
        assert call_kwargs["checkout_callback_urls"] == {
            "success_url": "https://example.com/success",
            "cancelled_url": "https://example.com/cancelled",
        }

    def test_changes_rate_card_with_upgrade_behavior(self, mock_lark_client):
        """Changes rate card with upgrade_behavior option."""
        change_subscription_rate_card(
            "sub_123",
            rate_card_id="rc_enterprise",
            upgrade_behavior="prorate",
        )

        call_kwargs = mock_lark_client.subscriptions.change_rate_card.call_args.kwargs
        assert call_kwargs["upgrade_behavior"] == "prorate"

    def test_raises_on_api_error(self, mock_lark_client):
        """Raises APIError when API call fails."""
        mock_request = MagicMock()
        mock_lark_client.subscriptions.change_rate_card.side_effect = lark.APIError(
            "Error", mock_request, body=None
        )

        with pytest.raises(lark.APIError):
            change_subscription_rate_card("sub_123", rate_card_id="rc_enterprise")


class TestChangeSubscriptionRateCardForUser:
    """Tests for change_subscription_rate_card_for_user function."""

    def test_changes_rate_card_owned_by_user(self, mock_user, mock_lark_client):
        """Changes rate card when subscription belongs to user."""
        # Set up subscription to be owned by user's external_id
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="test@example.com",
            status="active",
        )

        result = change_subscription_rate_card_for_user(
            mock_user, "sub_123", rate_card_id="rc_enterprise"
        )

        mock_lark_client.subscriptions.change_rate_card.assert_called_once_with(
            "sub_123",
            rate_card_id="rc_enterprise",
        )
        assert result.result.type == "requires_action"

    def test_changes_rate_card_with_subject_id_match(self, mock_user, mock_lark_client):
        """Changes rate card when subject_id matches resolved subject."""
        # Subscription has internal subject_id, not external_id
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="subj_123",
            status="active",
        )
        mock_lark_client.subjects.retrieve.return_value = MagicMock(
            id="subj_123",
            external_id="test@example.com",
        )

        result = change_subscription_rate_card_for_user(
            mock_user, "sub_123", rate_card_id="rc_enterprise"
        )

        mock_lark_client.subscriptions.change_rate_card.assert_called_once()
        assert result.result.type == "requires_action"

    def test_passes_callback_urls(self, mock_user, mock_lark_client):
        """Passes callback URLs to change_rate_card."""
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="test@example.com",
            status="active",
        )

        change_subscription_rate_card_for_user(
            mock_user,
            "sub_123",
            rate_card_id="rc_enterprise",
            success_url="https://example.com/success",
            cancelled_url="https://example.com/cancelled",
        )

        call_kwargs = mock_lark_client.subscriptions.change_rate_card.call_args.kwargs
        assert call_kwargs["checkout_callback_urls"] == {
            "success_url": "https://example.com/success",
            "cancelled_url": "https://example.com/cancelled",
        }

    def test_passes_upgrade_behavior(self, mock_user, mock_lark_client):
        """Passes upgrade_behavior to change_rate_card."""
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="test@example.com",
            status="active",
        )

        change_subscription_rate_card_for_user(
            mock_user,
            "sub_123",
            rate_card_id="rc_enterprise",
            upgrade_behavior="rate_difference",
        )

        call_kwargs = mock_lark_client.subscriptions.change_rate_card.call_args.kwargs
        assert call_kwargs["upgrade_behavior"] == "rate_difference"

    def test_raises_permission_error_for_wrong_user(self, mock_user, mock_lark_client):
        """Raises PermissionError when subscription belongs to another user."""
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="other_user@example.com",
            status="active",
        )
        mock_response = MagicMock()
        mock_lark_client.subjects.retrieve.side_effect = lark.NotFoundError(
            "Not found", response=mock_response, body=None
        )

        with pytest.raises(PermissionError, match="does not belong to this user"):
            change_subscription_rate_card_for_user(
                mock_user, "sub_123", rate_card_id="rc_enterprise"
            )

    def test_raises_permission_error_when_subject_mismatch(self, mock_user, mock_lark_client):
        """Raises PermissionError when subject lookup shows different owner."""
        mock_lark_client.subscriptions.retrieve.return_value = MagicMock(
            id="sub_123",
            subject_id="subj_other",
            status="active",
        )
        mock_lark_client.subjects.retrieve.return_value = MagicMock(
            id="subj_123",  # Different from subscription's subject_id
            external_id="test@example.com",
        )

        with pytest.raises(PermissionError, match="does not belong to this user"):
            change_subscription_rate_card_for_user(
                mock_user, "sub_123", rate_card_id="rc_enterprise"
            )


class TestRecordUsage:
    """Tests for record_usage function."""

    def test_records_usage(self, mock_lark_client):
        """Records a usage event."""
        result = record_usage(
            subject_id="user_123",
            event_name="api_calls",
            data={"count": 100},
            idempotency_key="key_123",
        )

        mock_lark_client.usage_events.create.assert_called_once_with(
            subject_id="user_123",
            event_name="api_calls",
            data={"count": 100},
            idempotency_key="key_123",
        )
        assert result.id == "evt_123"

    def test_records_usage_with_timestamp(self, mock_lark_client):
        """Records a usage event with timestamp."""
        from datetime import datetime, timezone

        ts = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        record_usage(
            subject_id="user_123",
            event_name="api_calls",
            data={"count": 100},
            idempotency_key="key_123",
            timestamp=ts,
        )

        call_kwargs = mock_lark_client.usage_events.create.call_args.kwargs
        assert call_kwargs["timestamp"] == ts

    def test_raises_on_api_error(self, mock_lark_client):
        """Raises APIError when API call fails."""
        mock_request = MagicMock()
        mock_lark_client.usage_events.create.side_effect = lark.APIError(
            "Error", mock_request, body=None
        )

        with pytest.raises(lark.APIError):
            record_usage(
                subject_id="user_123",
                event_name="api_calls",
                data={"count": 100},
                idempotency_key="key_123",
            )


class TestRecordUsageForUser:
    """Tests for record_usage_for_user function."""

    def test_records_usage_for_user(self, mock_user, mock_lark_client):
        """Records a usage event for a Django user."""
        result = record_usage_for_user(
            mock_user,
            event_name="api_calls",
            data={"count": 100},
            idempotency_key="key_123",
        )

        mock_lark_client.usage_events.create.assert_called_once_with(
            subject_id="test@example.com",
            event_name="api_calls",
            data={"count": 100},
            idempotency_key="key_123",
        )
        assert result.id == "evt_123"

    def test_records_usage_with_timestamp(self, mock_user, mock_lark_client):
        """Records a usage event with timestamp."""
        from datetime import datetime, timezone

        ts = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        record_usage_for_user(
            mock_user,
            event_name="storage_gb",
            data={"amount": "50.5"},
            idempotency_key="key_456",
            timestamp=ts,
        )

        call_kwargs = mock_lark_client.usage_events.create.call_args.kwargs
        assert call_kwargs["subject_id"] == "test@example.com"
        assert call_kwargs["timestamp"] == ts


@pytest.mark.asyncio
class TestAsyncFunctions:
    """Tests for async utility functions."""

    async def test_aget_billing_state_for_user(self, mock_user):
        """Async version returns billing state."""
        with patch("django_lark.utils.get_async_lark_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            async def async_retrieve(external_id):
                return MagicMock(has_active_subscription=True)

            mock_client.customer_access.retrieve_billing_state = async_retrieve

            billing_state = await aget_billing_state_for_user(mock_user)
            assert billing_state.has_active_subscription is True

    async def test_aget_subscriptions_for_user(self, mock_user):
        """Async version returns subscriptions."""
        with patch("django_lark.utils.get_async_lark_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            async def async_list(subject_id):
                return MagicMock(subscriptions=[MagicMock(id="sub_1")], has_more=False)

            mock_client.subscriptions.list = async_list

            result = await aget_subscriptions_for_user(mock_user)
            assert len(result.subscriptions) == 1

    async def test_aget_or_create_subject_for_user(self, mock_user):
        """Async version gets or creates subject."""
        with patch("django_lark.utils.get_async_lark_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            async def async_retrieve(external_id):
                return MagicMock(id="subj_123")

            mock_client.subjects.retrieve = async_retrieve

            subject, created = await aget_or_create_subject_for_user(mock_user)
            assert subject.id == "subj_123"
            assert created is False

    async def test_acreate_subscription_for_user(self, mock_user):
        """Async version creates subscription."""
        with patch("django_lark.utils.get_async_lark_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            async def async_create(**kwargs):
                return MagicMock(
                    result=MagicMock(
                        result_type="requires_action",
                        action=MagicMock(
                            checkout_url="https://checkout.uselark.ai/sub_new",
                        ),
                    ),
                )

            mock_client.subscriptions.create = async_create

            result = await acreate_subscription_for_user(
                mock_user,
                rate_card_id="rc_pro",
                success_url="https://example.com/success",
            )
            assert result.result.result_type == "requires_action"
            assert result.result.action.checkout_url == "https://checkout.uselark.ai/sub_new"

    async def test_acancel_subscription(self):
        """Async version cancels subscription."""
        with patch("django_lark.utils.get_async_lark_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            async def async_cancel(subscription_id):
                return MagicMock(id=subscription_id, status="cancelled")

            mock_client.subscriptions.cancel = async_cancel

            result = await acancel_subscription("sub_123")
            assert result.status == "cancelled"

    async def test_acancel_subscription_for_user(self, mock_user):
        """Async version cancels subscription with ownership check."""
        with patch("django_lark.utils.get_async_lark_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            async def async_retrieve(subscription_id):
                return MagicMock(
                    id=subscription_id,
                    subject_id="test@example.com",
                    status="active",
                )

            async def async_cancel(subscription_id):
                return MagicMock(id=subscription_id, status="cancelled")

            mock_client.subscriptions.retrieve = async_retrieve
            mock_client.subscriptions.cancel = async_cancel

            result = await acancel_subscription_for_user(mock_user, "sub_123")
            assert result.status == "cancelled"

    async def test_achange_subscription_rate_card(self):
        """Async version changes subscription rate card."""
        with patch("django_lark.utils.get_async_lark_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            async def async_change_rate_card(subscription_id, **kwargs):
                return MagicMock(
                    result=MagicMock(
                        type="requires_action",
                        action=MagicMock(
                            checkout_url="https://checkout.uselark.ai/change_rc",
                        ),
                    ),
                )

            mock_client.subscriptions.change_rate_card = async_change_rate_card

            result = await achange_subscription_rate_card(
                "sub_123",
                rate_card_id="rc_enterprise",
                success_url="https://example.com/success",
            )
            assert result.result.type == "requires_action"
            assert result.result.action.checkout_url == "https://checkout.uselark.ai/change_rc"

    async def test_achange_subscription_rate_card_for_user(self, mock_user):
        """Async version changes subscription rate card with ownership check."""
        with patch("django_lark.utils.get_async_lark_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            async def async_retrieve(subscription_id):
                return MagicMock(
                    id=subscription_id,
                    subject_id="test@example.com",
                    status="active",
                )

            async def async_change_rate_card(subscription_id, **kwargs):
                return MagicMock(
                    result=MagicMock(
                        type="success",
                        subscription=MagicMock(
                            id=subscription_id,
                            rate_card_id=kwargs.get("rate_card_id"),
                        ),
                    ),
                )

            mock_client.subscriptions.retrieve = async_retrieve
            mock_client.subscriptions.change_rate_card = async_change_rate_card

            result = await achange_subscription_rate_card_for_user(
                mock_user, "sub_123", rate_card_id="rc_enterprise"
            )
            assert result.result.type == "success"

    async def test_arecord_usage(self):
        """Async version records usage event."""
        with patch("django_lark.utils.get_async_lark_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            async def async_create(**kwargs):
                return MagicMock(id="evt_123", event_name=kwargs.get("event_name"))

            mock_client.usage_events.create = async_create

            result = await arecord_usage(
                subject_id="user_123",
                event_name="api_calls",
                data={"count": 100},
                idempotency_key="key_123",
            )
            assert result.id == "evt_123"
            assert result.event_name == "api_calls"

    async def test_arecord_usage_for_user(self, mock_user):
        """Async version records usage event for user."""
        with patch("django_lark.utils.get_async_lark_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            async def async_create(**kwargs):
                return MagicMock(
                    id="evt_123",
                    event_name=kwargs.get("event_name"),
                    subject_id=kwargs.get("subject_id"),
                )

            mock_client.usage_events.create = async_create

            result = await arecord_usage_for_user(
                mock_user,
                event_name="api_calls",
                data={"count": 100},
                idempotency_key="key_123",
            )
            assert result.id == "evt_123"
            assert result.subject_id == "test@example.com"
