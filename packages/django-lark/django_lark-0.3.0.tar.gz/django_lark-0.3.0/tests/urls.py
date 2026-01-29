"""
URL configuration for tests.
"""

from django.urls import include, path

urlpatterns = [
    path("billing/", include("django_lark.urls")),
]
