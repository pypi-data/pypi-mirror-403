"""
Django template tags for Lark billing.
"""

from django import template

from ..client import get_lark_client
from ..utils import get_external_id_for_user

register = template.Library()


@register.simple_tag(takes_context=True)
def has_active_subscription(context, user=None):
    """
    Check if user has an active subscription.

    Usage:
        {% load lark_tags %}
        {% has_active_subscription as is_subscribed %}
        {% if is_subscribed %}
            Premium content here
        {% endif %}

        {# Or with explicit user #}
        {% has_active_subscription user as is_subscribed %}
    """
    if user is None:
        user = context.get("user")

    if not user or not getattr(user, "is_authenticated", False):
        return False

    billing_state = _get_billing_state(user)
    if billing_state is None:
        return False

    return billing_state.has_active_subscription


@register.simple_tag(takes_context=True)
def get_billing_state(context, user=None):
    """
    Get full billing state for template use.

    Usage:
        {% load lark_tags %}
        {% get_billing_state as billing %}
        {% if billing.has_active_subscription %}
            <p>You have an active subscription!</p>
        {% endif %}
    """
    if user is None:
        user = context.get("user")

    if not user or not getattr(user, "is_authenticated", False):
        return None

    return _get_billing_state(user)


@register.simple_tag(takes_context=True)
def get_subscriptions(context, user=None):
    """
    Get list of subscriptions for user.

    Usage:
        {% get_subscriptions as subscriptions %}
        {% for sub in subscriptions %}
            <p>{{ sub.rate_card_id }} - {{ sub.status }}</p>
        {% endfor %}
    """
    if user is None:
        user = context.get("user")

    if not user or not getattr(user, "is_authenticated", False):
        return []

    external_id = get_external_id_for_user(user)
    client = get_lark_client()
    response = client.subscriptions.list(subject_id=external_id)
    return response.subscriptions


@register.simple_tag(takes_context=True)
def has_subscription_to_rate_card(context, rate_card_id, user=None):
    """
    Check if user has an active subscription to a specific rate card.

    Usage:
        {% has_subscription_to_rate_card "rc_premium_monthly" as has_premium %}
        {% if has_premium %}
            Premium features unlocked!
        {% endif %}
    """
    if user is None:
        user = context.get("user")

    if not user or not getattr(user, "is_authenticated", False):
        return False

    billing_state = _get_billing_state(user)
    if billing_state is None:
        return False

    for sub in billing_state.active_subscriptions or []:
        if sub.rate_card_id == rate_card_id:
            return True

    return False


@register.simple_tag(takes_context=True)
def get_lark_external_id(context, user=None):
    """
    Get the Lark external_id for a user.

    Usage:
        {% get_lark_external_id as external_id %}
        {% if external_id %}
            External ID: {{ external_id }}
        {% endif %}
    """
    if user is None:
        user = context.get("user")

    if not user or not getattr(user, "is_authenticated", False):
        return None

    return get_external_id_for_user(user)


@register.filter
def lark_subscription_status_badge(status):
    """
    Convert subscription status to a Bootstrap badge class.

    Usage:
        <span class="badge {{ subscription.status|lark_subscription_status_badge }}">
            {{ subscription.status }}
        </span>
    """
    badge_classes = {
        "active": "bg-success",
        "cancelled": "bg-danger",
        "paused": "bg-warning",
        "trialing": "bg-info",
    }
    return badge_classes.get(status, "bg-secondary")


def _get_billing_state(user):
    """Get billing state for user."""
    external_id = get_external_id_for_user(user)
    client = get_lark_client()
    return client.customer_access.retrieve_billing_state(external_id)
