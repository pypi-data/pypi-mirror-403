"""
Django settings for tests.
"""

SECRET_KEY = "test-secret-key-for-django-lark"

DEBUG = True

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django_lark",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True

ROOT_URLCONF = "tests.urls"

# Lark settings for tests
LARK_API_KEY = "test_api_key"
LARK_BASE_URL = "https://test.api.uselark.ai"
