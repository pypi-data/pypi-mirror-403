"""
URL patterns for django-lark.
"""

from django.urls import path

from . import views

app_name = "django_lark"

urlpatterns = [
    path("portal/", views.customer_portal_redirect, name="customer_portal"),
    path("checkout/", views.checkout_redirect, name="checkout"),
    path("change-rate-card/", views.change_rate_card_redirect, name="change_rate_card"),
]
