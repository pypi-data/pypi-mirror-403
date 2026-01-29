"""
Django app configuration for django-lark.
"""

from django.apps import AppConfig


class DjangoLarkConfig(AppConfig):
    """Django Lark application configuration."""

    name = "django_lark"
    verbose_name = "Lark Billing"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Perform initialization when Django starts."""
        # Import checks to register them
        from . import checks  # noqa: F401
