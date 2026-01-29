"""
Django Lark configuration module.

Settings are read from Django settings with LARK_ prefix.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured


@dataclass
class LarkSettings:
    """Container for Lark configuration settings."""

    # Required
    api_key: str = ""

    # Optional with defaults
    base_url: str = "https://api.uselark.ai"
    timeout: float = 60.0
    max_retries: int = 2

    # User linking configuration
    user_subject_field: str = "email"
    auto_create_subjects: bool = False

    # Admin configuration
    admin_readonly: bool = True

    # Caching
    client_cache_enabled: bool = False

    def __post_init__(self):
        """Validate settings after initialization."""
        if not self.api_key:
            raise ImproperlyConfigured(
                "LARK_API_KEY must be set in Django settings or environment."
            )


def get_lark_settings() -> LarkSettings:
    """
    Load Lark settings from Django settings.

    Settings are prefixed with LARK_ in Django settings.
    Falls back to environment variables for api_key and base_url.

    Returns:
        LarkSettings: Configured settings object.

    Raises:
        ImproperlyConfigured: If required settings are missing.
    """
    # Get API key from settings or environment
    api_key = getattr(django_settings, "LARK_API_KEY", None)
    if api_key is None:
        api_key = os.environ.get("LARK_API_KEY", "")

    # Get base URL from settings or environment
    base_url = getattr(django_settings, "LARK_BASE_URL", None)
    if base_url is None:
        base_url = os.environ.get("LARK_BASE_URL", "https://api.uselark.ai")

    return LarkSettings(
        api_key=api_key,
        base_url=base_url,
        timeout=getattr(django_settings, "LARK_TIMEOUT", 60.0),
        max_retries=getattr(django_settings, "LARK_MAX_RETRIES", 2),
        user_subject_field=getattr(django_settings, "LARK_USER_SUBJECT_FIELD", "email"),
        auto_create_subjects=getattr(
            django_settings, "LARK_AUTO_CREATE_SUBJECTS", False
        ),
        admin_readonly=getattr(django_settings, "LARK_ADMIN_READONLY", True),
        client_cache_enabled=getattr(
            django_settings, "LARK_CLIENT_CACHE_ENABLED", True
        ),
    )


# Lazy singleton
_settings: Optional[LarkSettings] = None


def get_settings() -> LarkSettings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = get_lark_settings()
    return _settings


def clear_settings_cache() -> None:
    """Clear cached settings. Useful for testing."""
    global _settings
    _settings = None
