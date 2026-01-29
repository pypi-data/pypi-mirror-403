"""
Django system checks for django-lark.
"""

from typing import Any, List

from django.conf import settings
from django.core.checks import CheckMessage, Error, Warning, register


@register()
def check_lark_settings(app_configs: Any, **kwargs: Any) -> List[CheckMessage]:
    """Check that Lark settings are properly configured."""
    errors: List[CheckMessage] = []

    # Check for API key
    api_key = getattr(settings, "LARK_API_KEY", None)
    if not api_key:
        import os

        api_key = os.environ.get("LARK_API_KEY")

    if not api_key:
        errors.append(
            Warning(
                "LARK_API_KEY is not configured.",
                hint="Set LARK_API_KEY in your Django settings or environment variables.",
                id="django_lark.W001",
            )
        )

    # Check base URL format
    base_url = getattr(settings, "LARK_BASE_URL", None)
    if base_url and not base_url.startswith(("http://", "https://")):
        errors.append(
            Error(
                "LARK_BASE_URL must start with http:// or https://",
                hint=f"Current value: {base_url}",
                id="django_lark.E001",
            )
        )

    # Check timeout is positive
    timeout = getattr(settings, "LARK_TIMEOUT", None)
    if timeout is not None and timeout <= 0:
        errors.append(
            Error(
                "LARK_TIMEOUT must be a positive number.",
                hint=f"Current value: {timeout}",
                id="django_lark.E002",
            )
        )

    # Check max_retries is non-negative
    max_retries = getattr(settings, "LARK_MAX_RETRIES", None)
    if max_retries is not None and max_retries < 0:
        errors.append(
            Error(
                "LARK_MAX_RETRIES must be a non-negative integer.",
                hint=f"Current value: {max_retries}",
                id="django_lark.E003",
            )
        )

    return errors
