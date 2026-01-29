"""
Utility functions for django-lark.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional, Tuple, Union

import lark

from .client import get_async_lark_client, get_lark_client
from .conf import get_settings

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    from .conf import LarkSettings

# Type alias for subject return types (create returns SubjectCreateResponse, retrieve returns SubjectResource)
SubjectResult = Union["lark.types.SubjectResource", "lark.types.SubjectCreateResponse"]


def get_external_id_for_user(user: AbstractUser) -> str:
    """
    Get the Lark external_id for a Django user.

    The external_id is computed based on the LARK_USER_SUBJECT_FIELD setting.
    This can be passed directly to Lark API methods that accept subject_id,
    as Lark's API accepts external_id anywhere a subject_id is expected.

    Args:
        user: Django user instance.

    Returns:
        The external_id string for the user.
    """
    settings = get_settings()
    return _get_user_external_id(user, settings)


def get_or_create_subject_for_user(
    user: AbstractUser,
    *,
    create_if_missing: bool = True,
    update_if_exists: bool = False,
) -> Tuple[SubjectResult, bool]:
    """
    Get or create a Lark subject for a Django user.

    Uses the user's external_id to look up or create the subject in Lark.
    No local database records are created.

    Args:
        user: Django user instance.
        create_if_missing: If True, create subject in Lark if not found.
        update_if_exists: If True, update Lark subject with user data.

    Returns:
        Tuple of (SubjectResource, created: bool)

    Raises:
        lark.APIError: If API call fails.
        lark.NotFoundError: If subject not found and create_if_missing=False.
    """
    client = get_lark_client()
    external_id = get_external_id_for_user(user)
    created = False
    subject: SubjectResult

    # Try to retrieve existing subject by external_id
    try:
        subject = client.subjects.retrieve(external_id)

        if update_if_exists:
            subject = client.subjects.update(
                external_id,
                name=_get_user_name(user),
                email=getattr(user, "email", None),
            )

        return subject, created

    except lark.NotFoundError:
        pass

    # Create new subject if allowed
    if create_if_missing:
        subject = client.subjects.create(
            name=_get_user_name(user),
            email=getattr(user, "email", None),
            external_id=external_id,
        )
        created = True
        return subject, created

    # Re-raise the original NotFoundError if create_if_missing is False
    raise LookupError(f"No Lark subject found for user {user}")


async def aget_or_create_subject_for_user(
    user: AbstractUser,
    *,
    create_if_missing: bool = True,
    update_if_exists: bool = False,
) -> Tuple[SubjectResult, bool]:
    """Async version of get_or_create_subject_for_user."""
    client = get_async_lark_client()
    external_id = get_external_id_for_user(user)
    created = False
    subject: SubjectResult

    # Try to retrieve existing subject by external_id
    try:
        subject = await client.subjects.retrieve(external_id)

        if update_if_exists:
            subject = await client.subjects.update(
                external_id,
                name=_get_user_name(user),
                email=getattr(user, "email", None),
            )

        return subject, created

    except lark.NotFoundError:
        pass

    # Create new subject if allowed
    if create_if_missing:
        subject = await client.subjects.create(
            name=_get_user_name(user),
            email=getattr(user, "email", None),
            external_id=external_id,
        )
        created = True
        return subject, created

    raise LookupError(f"No Lark subject found for user {user}")


def get_billing_state_for_user(user: AbstractUser):
    """
    Get billing state for a Django user.

    Uses the user's external_id to look up their billing state in Lark.

    Args:
        user: Django user instance.

    Returns:
        BillingState from Lark API.

    Raises:
        lark.APIError: If the API call fails.
    """
    external_id = get_external_id_for_user(user)
    client = get_lark_client()
    return client.customer_access.retrieve_billing_state(external_id)


async def aget_billing_state_for_user(user: AbstractUser):
    """Async version of get_billing_state_for_user."""
    external_id = get_external_id_for_user(user)
    client = get_async_lark_client()
    return await client.customer_access.retrieve_billing_state(external_id)


def get_subscriptions_for_user(user: AbstractUser):
    """
    Get subscriptions for a Django user.

    Uses the user's external_id to look up their subscriptions in Lark.

    Args:
        user: Django user instance.

    Returns:
        List of subscriptions from Lark API.

    Raises:
        lark.APIError: If the API call fails.
    """
    external_id = get_external_id_for_user(user)
    client = get_lark_client()
    return client.subscriptions.list(subject_id=external_id)


async def aget_subscriptions_for_user(user: AbstractUser):
    """Async version of get_subscriptions_for_user."""
    external_id = get_external_id_for_user(user)
    client = get_async_lark_client()
    return await client.subscriptions.list(subject_id=external_id)


def create_subscription_for_user(
    user: AbstractUser,
    rate_card_id: str,
    *,
    success_url: Optional[str] = None,
    cancelled_url: Optional[str] = None,
    create_checkout_session: Optional[str] = None,
    fixed_rate_quantities: Optional[dict] = None,
    rate_price_multipliers: Optional[dict] = None,
    metadata: Optional[dict] = None,
):
    """
    Create a subscription for a Django user.

    This creates a subscription in Lark and returns a checkout session.
    The user should be redirected to the checkout URL to complete payment.

    Args:
        user: Django user instance.
        rate_card_id: The rate card ID to subscribe to.
        success_url: URL to redirect to after successful checkout.
        cancelled_url: URL to redirect to if checkout is cancelled.
        create_checkout_session: When to create a checkout session.
            "when_required" (default) - only if payment method needed.
            "always" - always create checkout even if payment method on file.
        fixed_rate_quantities: Quantities for fixed rates, as a dict mapping
            rate code to quantity (e.g., {"seats": 5, "storage_gb": 100}).
        rate_price_multipliers: Price multipliers for rates, as a dict mapping
            rate code to multiplier (e.g., {"seats": 0.8} for 20% discount).
        metadata: Optional metadata to attach to the subscription.

    Returns:
        Subscription object from Lark API with checkout_url attribute.

    Raises:
        lark.APIError: If the API call fails.

    Example:
        subscription = create_subscription_for_user(
            user,
            rate_card_id="rc_pro",
            success_url="https://example.com/welcome",
            cancelled_url="https://example.com/pricing",
            fixed_rate_quantities={"seats": 5},
            rate_price_multipliers={"seats": 0.9},  # 10% discount
        )
        return redirect(subscription.checkout_url)
    """
    external_id = get_external_id_for_user(user)
    client = get_lark_client()

    kwargs: dict = {
        "rate_card_id": rate_card_id,
        "subject_id": external_id,
    }

    if success_url or cancelled_url:
        kwargs["checkout_callback_urls"] = {}
        if success_url:
            kwargs["checkout_callback_urls"]["success_url"] = success_url
        if cancelled_url:
            kwargs["checkout_callback_urls"]["cancelled_url"] = cancelled_url

    if create_checkout_session:
        kwargs["create_checkout_session"] = create_checkout_session

    if fixed_rate_quantities:
        kwargs["fixed_rate_quantities"] = fixed_rate_quantities

    if rate_price_multipliers:
        kwargs["rate_price_multipliers"] = rate_price_multipliers

    if metadata:
        kwargs["metadata"] = metadata

    return client.subscriptions.create(**kwargs)


async def acreate_subscription_for_user(
    user: AbstractUser,
    rate_card_id: str,
    *,
    success_url: Optional[str] = None,
    cancelled_url: Optional[str] = None,
    create_checkout_session: Optional[str] = None,
    fixed_rate_quantities: Optional[dict] = None,
    rate_price_multipliers: Optional[dict] = None,
    metadata: Optional[dict] = None,
):
    """Async version of create_subscription_for_user."""
    external_id = get_external_id_for_user(user)
    client = get_async_lark_client()

    kwargs: dict = {
        "rate_card_id": rate_card_id,
        "subject_id": external_id,
    }

    if success_url or cancelled_url:
        kwargs["checkout_callback_urls"] = {}
        if success_url:
            kwargs["checkout_callback_urls"]["success_url"] = success_url
        if cancelled_url:
            kwargs["checkout_callback_urls"]["cancelled_url"] = cancelled_url

    if create_checkout_session:
        kwargs["create_checkout_session"] = create_checkout_session

    if fixed_rate_quantities:
        kwargs["fixed_rate_quantities"] = fixed_rate_quantities

    if rate_price_multipliers:
        kwargs["rate_price_multipliers"] = rate_price_multipliers

    if metadata:
        kwargs["metadata"] = metadata

    return await client.subscriptions.create(**kwargs)


def cancel_subscription(subscription_id: str):
    """
    Cancel a subscription.

    Args:
        subscription_id: The subscription ID to cancel.

    Returns:
        Cancelled subscription object from Lark API.

    Raises:
        lark.APIError: If the API call fails.
        lark.NotFoundError: If subscription not found.
    """
    client = get_lark_client()
    return client.subscriptions.cancel(subscription_id)


async def acancel_subscription(subscription_id: str):
    """Async version of cancel_subscription."""
    client = get_async_lark_client()
    return await client.subscriptions.cancel(subscription_id)


def cancel_subscription_for_user(user: AbstractUser, subscription_id: str):
    """
    Cancel a subscription for a user.

    This verifies the subscription belongs to the user before cancelling.

    Args:
        user: Django user instance.
        subscription_id: The subscription ID to cancel.

    Returns:
        Cancelled subscription object from Lark API.

    Raises:
        lark.APIError: If the API call fails.
        lark.NotFoundError: If subscription not found.
        PermissionError: If subscription doesn't belong to user.
    """
    external_id = get_external_id_for_user(user)
    client = get_lark_client()

    # Verify ownership
    subscription = client.subscriptions.retrieve(subscription_id)
    if subscription.subject_id != external_id:
        # Check if it matches by external_id lookup
        try:
            subject = client.subjects.retrieve(external_id)
            if subscription.subject_id != subject.id:
                raise PermissionError("Subscription does not belong to this user")
        except lark.NotFoundError:
            raise PermissionError("Subscription does not belong to this user")

    return client.subscriptions.cancel(subscription_id)


async def acancel_subscription_for_user(user: AbstractUser, subscription_id: str):
    """Async version of cancel_subscription_for_user."""
    external_id = get_external_id_for_user(user)
    client = get_async_lark_client()

    # Verify ownership
    subscription = await client.subscriptions.retrieve(subscription_id)
    if subscription.subject_id != external_id:
        try:
            subject = await client.subjects.retrieve(external_id)
            if subscription.subject_id != subject.id:
                raise PermissionError("Subscription does not belong to this user")
        except lark.NotFoundError:
            raise PermissionError("Subscription does not belong to this user")

    return await client.subscriptions.cancel(subscription_id)


def change_subscription_rate_card(
    subscription_id: str,
    rate_card_id: str,
    *,
    success_url: Optional[str] = None,
    cancelled_url: Optional[str] = None,
    upgrade_behavior: Optional[str] = None,
):
    """
    Change the rate card for an existing subscription.

    This allows upgrading or downgrading a subscription to a different rate card.
    May require checkout if additional payment is needed.

    Args:
        subscription_id: The subscription ID to change.
        rate_card_id: The new rate card ID to change to.
        success_url: URL to redirect to after successful checkout.
        cancelled_url: URL to redirect to if checkout is cancelled.
        upgrade_behavior: How to handle upgrades. Options:
            - "prorate": Charge for the prorated difference.
            - "rate_difference": Charge the difference without respect to time.

    Returns:
        Response from Lark API. Check result.type:
        - "success": Change completed, subscription returned.
        - "requires_action": Checkout needed, action.checkout_url provided.

    Raises:
        lark.APIError: If the API call fails.
        lark.NotFoundError: If subscription not found.

    Example:
        response = change_subscription_rate_card(
            "sub_123",
            rate_card_id="rc_enterprise",
            success_url="https://example.com/upgraded",
            upgrade_behavior="prorate",
        )
        if response.result.type == "requires_action":
            return redirect(response.result.action.checkout_url)
    """
    client = get_lark_client()

    kwargs: dict = {
        "rate_card_id": rate_card_id,
    }

    if success_url or cancelled_url:
        kwargs["checkout_callback_urls"] = {}
        if success_url:
            kwargs["checkout_callback_urls"]["success_url"] = success_url
        if cancelled_url:
            kwargs["checkout_callback_urls"]["cancelled_url"] = cancelled_url

    if upgrade_behavior:
        kwargs["upgrade_behavior"] = upgrade_behavior

    return client.subscriptions.change_rate_card(subscription_id, **kwargs)


async def achange_subscription_rate_card(
    subscription_id: str,
    rate_card_id: str,
    *,
    success_url: Optional[str] = None,
    cancelled_url: Optional[str] = None,
    upgrade_behavior: Optional[str] = None,
):
    """Async version of change_subscription_rate_card."""
    client = get_async_lark_client()

    kwargs: dict = {
        "rate_card_id": rate_card_id,
    }

    if success_url or cancelled_url:
        kwargs["checkout_callback_urls"] = {}
        if success_url:
            kwargs["checkout_callback_urls"]["success_url"] = success_url
        if cancelled_url:
            kwargs["checkout_callback_urls"]["cancelled_url"] = cancelled_url

    if upgrade_behavior:
        kwargs["upgrade_behavior"] = upgrade_behavior

    return await client.subscriptions.change_rate_card(subscription_id, **kwargs)


def change_subscription_rate_card_for_user(
    user: AbstractUser,
    subscription_id: str,
    rate_card_id: str,
    *,
    success_url: Optional[str] = None,
    cancelled_url: Optional[str] = None,
    upgrade_behavior: Optional[str] = None,
):
    """
    Change the rate card for a user's subscription.

    This verifies the subscription belongs to the user before changing it.

    Args:
        user: Django user instance.
        subscription_id: The subscription ID to change.
        rate_card_id: The new rate card ID to change to.
        success_url: URL to redirect to after successful checkout.
        cancelled_url: URL to redirect to if checkout is cancelled.
        upgrade_behavior: How to handle upgrades ("prorate" or "rate_difference").

    Returns:
        Response from Lark API with result.type indicating next steps.

    Raises:
        lark.APIError: If the API call fails.
        lark.NotFoundError: If subscription not found.
        PermissionError: If subscription doesn't belong to user.

    Example:
        response = change_subscription_rate_card_for_user(
            user,
            "sub_123",
            rate_card_id="rc_enterprise",
            success_url="https://example.com/upgraded",
        )
        if response.result.type == "requires_action":
            return redirect(response.result.action.checkout_url)
    """
    external_id = get_external_id_for_user(user)
    client = get_lark_client()

    # Verify ownership
    subscription = client.subscriptions.retrieve(subscription_id)
    if subscription.subject_id != external_id:
        # Check if it matches by external_id lookup
        try:
            subject = client.subjects.retrieve(external_id)
            if subscription.subject_id != subject.id:
                raise PermissionError("Subscription does not belong to this user")
        except lark.NotFoundError:
            raise PermissionError("Subscription does not belong to this user")

    kwargs: dict = {
        "rate_card_id": rate_card_id,
    }

    if success_url or cancelled_url:
        kwargs["checkout_callback_urls"] = {}
        if success_url:
            kwargs["checkout_callback_urls"]["success_url"] = success_url
        if cancelled_url:
            kwargs["checkout_callback_urls"]["cancelled_url"] = cancelled_url

    if upgrade_behavior:
        kwargs["upgrade_behavior"] = upgrade_behavior

    return client.subscriptions.change_rate_card(subscription_id, **kwargs)


async def achange_subscription_rate_card_for_user(
    user: AbstractUser,
    subscription_id: str,
    rate_card_id: str,
    *,
    success_url: Optional[str] = None,
    cancelled_url: Optional[str] = None,
    upgrade_behavior: Optional[str] = None,
):
    """Async version of change_subscription_rate_card_for_user."""
    external_id = get_external_id_for_user(user)
    client = get_async_lark_client()

    # Verify ownership
    subscription = await client.subscriptions.retrieve(subscription_id)
    if subscription.subject_id != external_id:
        try:
            subject = await client.subjects.retrieve(external_id)
            if subscription.subject_id != subject.id:
                raise PermissionError("Subscription does not belong to this user")
        except lark.NotFoundError:
            raise PermissionError("Subscription does not belong to this user")

    kwargs: dict = {
        "rate_card_id": rate_card_id,
    }

    if success_url or cancelled_url:
        kwargs["checkout_callback_urls"] = {}
        if success_url:
            kwargs["checkout_callback_urls"]["success_url"] = success_url
        if cancelled_url:
            kwargs["checkout_callback_urls"]["cancelled_url"] = cancelled_url

    if upgrade_behavior:
        kwargs["upgrade_behavior"] = upgrade_behavior

    return await client.subscriptions.change_rate_card(subscription_id, **kwargs)


def record_usage(
    subject_id: str,
    event_name: str,
    data: Dict[str, Union[str, int]],
    idempotency_key: str,
    *,
    timestamp: Optional[datetime] = None,
):
    """
    Record a usage event for metered billing.

    Usage events are used to track consumption for usage-based pricing.
    The event_name and data should match the pricing metrics configured
    in your Lark rate cards.

    Args:
        subject_id: The subject ID or external_id for the user.
        event_name: The name of the event (must match pricing metric config).
        data: Usage data dict (e.g., {"compute_hours": "100.5"}).
        idempotency_key: Unique key to prevent duplicate events.
        timestamp: When the usage occurred. Defaults to current time.

    Returns:
        The created usage event from Lark API.

    Raises:
        lark.APIError: If the API call fails.

    Example:
        import uuid

        record_usage(
            subject_id="user_123",
            event_name="api_calls",
            data={"count": 100},
            idempotency_key=str(uuid.uuid4()),
        )
    """
    client = get_lark_client()

    kwargs: dict = {
        "subject_id": subject_id,
        "event_name": event_name,
        "data": data,
        "idempotency_key": idempotency_key,
    }

    if timestamp:
        kwargs["timestamp"] = timestamp

    return client.usage_events.create(**kwargs)


async def arecord_usage(
    subject_id: str,
    event_name: str,
    data: Dict[str, Union[str, int]],
    idempotency_key: str,
    *,
    timestamp: Optional[datetime] = None,
):
    """Async version of record_usage."""
    client = get_async_lark_client()

    kwargs: dict = {
        "subject_id": subject_id,
        "event_name": event_name,
        "data": data,
        "idempotency_key": idempotency_key,
    }

    if timestamp:
        kwargs["timestamp"] = timestamp

    return await client.usage_events.create(**kwargs)


def record_usage_for_user(
    user: "AbstractUser",
    event_name: str,
    data: Dict[str, Union[str, int]],
    idempotency_key: str,
    *,
    timestamp: Optional[datetime] = None,
):
    """
    Record a usage event for a Django user.

    Uses the user's external_id to identify them in Lark.

    Args:
        user: Django user instance.
        event_name: The name of the event (must match pricing metric config).
        data: Usage data dict (e.g., {"compute_hours": "100.5"}).
        idempotency_key: Unique key to prevent duplicate events.
        timestamp: When the usage occurred. Defaults to current time.

    Returns:
        The created usage event from Lark API.

    Raises:
        lark.APIError: If the API call fails.

    Example:
        import uuid

        record_usage_for_user(
            user,
            event_name="api_calls",
            data={"count": 100},
            idempotency_key=str(uuid.uuid4()),
        )

        # With timestamp
        from datetime import datetime, timezone

        record_usage_for_user(
            user,
            event_name="storage_gb",
            data={"amount": "50.5"},
            idempotency_key=f"storage_{user.pk}_{date}",
            timestamp=datetime.now(timezone.utc),
        )
    """
    external_id = get_external_id_for_user(user)
    return record_usage(
        subject_id=external_id,
        event_name=event_name,
        data=data,
        idempotency_key=idempotency_key,
        timestamp=timestamp,
    )


async def arecord_usage_for_user(
    user: "AbstractUser",
    event_name: str,
    data: Dict[str, Union[str, int]],
    idempotency_key: str,
    *,
    timestamp: Optional[datetime] = None,
):
    """Async version of record_usage_for_user."""
    external_id = get_external_id_for_user(user)
    return await arecord_usage(
        subject_id=external_id,
        event_name=event_name,
        data=data,
        idempotency_key=idempotency_key,
        timestamp=timestamp,
    )


def _get_user_name(user: AbstractUser) -> str:
    """Get display name for user."""
    if hasattr(user, "get_full_name") and user.get_full_name():
        return user.get_full_name()
    return str(user)


def _get_user_external_id(user: AbstractUser, settings: "LarkSettings") -> str:
    """Get external_id value based on settings."""
    field = settings.user_subject_field

    if callable(field):
        return str(field(user))

    if field == "id":
        return f"django_user_{user.pk}"

    return str(getattr(user, field, user.pk))
