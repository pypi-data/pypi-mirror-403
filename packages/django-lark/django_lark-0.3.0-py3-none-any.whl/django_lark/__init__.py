"""
Django Lark - Django integration for Lark billing.
"""

from .client import get_async_lark_client, get_lark_client
from .conf import get_settings
from .utils import (
    acancel_subscription,
    acancel_subscription_for_user,
    achange_subscription_rate_card,
    achange_subscription_rate_card_for_user,
    acreate_subscription_for_user,
    arecord_usage,
    arecord_usage_for_user,
    cancel_subscription,
    cancel_subscription_for_user,
    change_subscription_rate_card,
    change_subscription_rate_card_for_user,
    create_subscription_for_user,
    get_external_id_for_user,
    record_usage,
    record_usage_for_user,
)

__version__ = "0.1.0"
__all__ = [
    "get_lark_client",
    "get_async_lark_client",
    "get_settings",
    "get_external_id_for_user",
    "create_subscription_for_user",
    "acreate_subscription_for_user",
    "cancel_subscription",
    "acancel_subscription",
    "cancel_subscription_for_user",
    "acancel_subscription_for_user",
    "change_subscription_rate_card",
    "achange_subscription_rate_card",
    "change_subscription_rate_card_for_user",
    "achange_subscription_rate_card_for_user",
    "record_usage",
    "arecord_usage",
    "record_usage_for_user",
    "arecord_usage_for_user",
]

default_app_config = "django_lark.apps.DjangoLarkConfig"
