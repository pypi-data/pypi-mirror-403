"""
Django views for Lark integration.
"""

import lark
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.views.decorators.http import require_http_methods

from .client import get_lark_client
from .utils import (
    change_subscription_rate_card_for_user,
    create_subscription_for_user,
    get_external_id_for_user,
)


@login_required
@require_http_methods(["GET"])
def customer_portal_redirect(request):
    """
    Redirect user to their Lark customer portal.

    Creates a portal session and redirects to the portal URL.
    Uses the user's external_id to identify them in Lark.

    Query params:
        return_url: Optional URL to return to after portal visit.
    """
    user = request.user
    return_url = request.GET.get("return_url", request.build_absolute_uri("/"))
    external_id = get_external_id_for_user(user)

    try:
        client = get_lark_client()
        session = client.customer_portal.create_session(
            subject_id=external_id,  # Lark accepts external_id here
            return_url=return_url,
        )
        return HttpResponseRedirect(session.url)
    except lark.APIError as e:
        return HttpResponseBadRequest(f"Unable to create portal session: {e}")


@login_required
@require_http_methods(["GET", "POST"])
def checkout_redirect(request):
    """
    Create a subscription and redirect user to Lark checkout.

    This view creates a subscription for the authenticated user and
    redirects them to the Lark-hosted checkout page to complete payment.

    Query params / POST data:
        rate_card_id: Required. The rate card ID to subscribe to.
        success_url: Optional URL to redirect to after successful checkout.
        cancelled_url: Optional URL to redirect to if checkout is cancelled.

    Returns:
        302 redirect to Lark checkout URL.

    Example usage in templates:
        <a href="{% url 'django_lark:checkout' %}?rate_card_id=rc_pro&success_url=/welcome/">
            Subscribe to Pro
        </a>

        <form method="post" action="{% url 'django_lark:checkout' %}">
            {% csrf_token %}
            <input type="hidden" name="rate_card_id" value="rc_pro">
            <input type="hidden" name="success_url" value="/welcome/">
            <button type="submit">Subscribe</button>
        </form>
    """
    user = request.user

    # Get parameters from GET or POST
    if request.method == "POST":
        rate_card_id = request.POST.get("rate_card_id")
        success_url = request.POST.get("success_url")
        cancelled_url = request.POST.get("cancelled_url")
    else:
        rate_card_id = request.GET.get("rate_card_id")
        success_url = request.GET.get("success_url")
        cancelled_url = request.GET.get("cancelled_url")

    if not rate_card_id:
        return HttpResponseBadRequest("rate_card_id is required")

    # Build absolute URLs if relative paths provided
    if success_url and not success_url.startswith(("http://", "https://")):
        success_url = request.build_absolute_uri(success_url)
    if cancelled_url and not cancelled_url.startswith(("http://", "https://")):
        cancelled_url = request.build_absolute_uri(cancelled_url)

    try:
        response = create_subscription_for_user(
            user,
            rate_card_id=rate_card_id,
            success_url=success_url,
            cancelled_url=cancelled_url,
        )

        # Handle response based on result type
        if response.result.result_type == "requires_action":
            # Redirect to checkout
            return HttpResponseRedirect(response.result.action.checkout_url)
        else:
            # Subscription created directly (no checkout needed)
            # Redirect to success URL or home
            redirect_url = success_url or request.build_absolute_uri("/")
            return HttpResponseRedirect(redirect_url)
    except lark.APIError as e:
        return HttpResponseBadRequest(f"Unable to create subscription: {e}")


@login_required
@require_http_methods(["GET", "POST"])
def change_rate_card_redirect(request):
    """
    Change the rate card for an existing subscription and redirect to checkout if needed.

    This view changes the rate card for a user's subscription and redirects
    them to the Lark-hosted checkout page if additional payment is required.

    Query params / POST data:
        subscription_id: Required. The subscription ID to change.
        rate_card_id: Required. The new rate card ID to change to.
        success_url: Optional URL to redirect to after successful checkout.
        cancelled_url: Optional URL to redirect to if checkout is cancelled.
        upgrade_behavior: Optional. How to handle upgrades:
            - "prorate": Charge for the prorated difference.
            - "rate_difference": Charge the difference without respect to time.

    Returns:
        302 redirect to Lark checkout URL or success URL.

    Example usage in templates:
        <a href="{% url 'django_lark:change_rate_card' %}?subscription_id=sub_123&rate_card_id=rc_enterprise">
            Upgrade to Enterprise
        </a>

        <form method="post" action="{% url 'django_lark:change_rate_card' %}">
            {% csrf_token %}
            <input type="hidden" name="subscription_id" value="{{ subscription.id }}">
            <input type="hidden" name="rate_card_id" value="rc_enterprise">
            <input type="hidden" name="success_url" value="/upgraded/">
            <button type="submit">Upgrade Plan</button>
        </form>
    """
    user = request.user

    # Get parameters from GET or POST
    if request.method == "POST":
        subscription_id = request.POST.get("subscription_id")
        rate_card_id = request.POST.get("rate_card_id")
        success_url = request.POST.get("success_url")
        cancelled_url = request.POST.get("cancelled_url")
        upgrade_behavior = request.POST.get("upgrade_behavior")
    else:
        subscription_id = request.GET.get("subscription_id")
        rate_card_id = request.GET.get("rate_card_id")
        success_url = request.GET.get("success_url")
        cancelled_url = request.GET.get("cancelled_url")
        upgrade_behavior = request.GET.get("upgrade_behavior")

    if not subscription_id:
        return HttpResponseBadRequest("subscription_id is required")

    if not rate_card_id:
        return HttpResponseBadRequest("rate_card_id is required")

    # Build absolute URLs if relative paths provided
    if success_url and not success_url.startswith(("http://", "https://")):
        success_url = request.build_absolute_uri(success_url)
    if cancelled_url and not cancelled_url.startswith(("http://", "https://")):
        cancelled_url = request.build_absolute_uri(cancelled_url)

    try:
        response = change_subscription_rate_card_for_user(
            user,
            subscription_id,
            rate_card_id=rate_card_id,
            success_url=success_url,
            cancelled_url=cancelled_url,
            upgrade_behavior=upgrade_behavior,
        )

        # Handle response based on result type
        if response.result.type == "requires_action":
            # Redirect to checkout
            return HttpResponseRedirect(response.result.action.checkout_url)
        else:
            # Rate card changed directly (no checkout needed)
            # Redirect to success URL or home
            redirect_url = success_url or request.build_absolute_uri("/")
            return HttpResponseRedirect(redirect_url)
    except PermissionError as e:
        return HttpResponseBadRequest(str(e))
    except lark.APIError as e:
        return HttpResponseBadRequest(f"Unable to change rate card: {e}")
