"""
View decorators for subscription-based access control and usage tracking.
"""

from datetime import datetime, timezone
import logging
import uuid
from functools import wraps
from typing import Callable, Dict, List, Optional, Union

import lark
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .client import get_lark_client
from .utils import get_external_id_for_user, record_usage_for_user

logger = logging.getLogger(__name__)


def subscription_required(
    rate_card_ids: Optional[List[str]] = None,
    redirect_url: Optional[str] = None,
):
    """
    Decorator that requires user to have an active subscription.

    Uses the user's external_id to look up their billing state in Lark.

    Args:
        rate_card_ids: Optional list of rate card IDs to check.
                       If None, any active subscription is sufficient.
        redirect_url: URL to redirect to if not subscribed.
                      If None, returns 403 Forbidden.

    Usage:
        @subscription_required()
        def premium_view(request):
            return render(request, 'premium.html')

        @subscription_required(rate_card_ids=['rc_pro', 'rc_enterprise'])
        def pro_view(request):
            return render(request, 'pro.html')

        @subscription_required(redirect_url='/pricing/')
        def feature_view(request):
            return render(request, 'feature.html')
    """

    def decorator(view_func: Callable):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                if redirect_url:
                    return redirect(redirect_url)
                return HttpResponseForbidden("Authentication required")

            # Check subscription using external_id
            try:
                external_id = get_external_id_for_user(user)
                client = get_lark_client()
                billing_state = client.customer_access.retrieve_billing_state(
                    external_id
                )

                if not billing_state.has_active_subscription:
                    if redirect_url:
                        return redirect(redirect_url)
                    return HttpResponseForbidden("Active subscription required")

                # Check specific rate cards if provided
                if rate_card_ids:
                    user_rate_cards = {
                        s.rate_card_id
                        for s in (billing_state.active_subscriptions or [])
                    }
                    if not any(rc in user_rate_cards for rc in rate_card_ids):
                        if redirect_url:
                            return redirect(redirect_url)
                        return HttpResponseForbidden(
                            "Required subscription tier not found"
                        )

            except lark.APIError:
                if redirect_url:
                    return redirect(redirect_url)
                return HttpResponseForbidden("Unable to verify subscription")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def usage_within_limits(
    redirect_url: Optional[str] = None,
):
    """
    Decorator that requires user's usage to be within included limits.

    Blocks access if the user has exceeded the included usage on any
    usage-based rate they are subscribed to (has_overage_for_usage is True).

    Args:
        redirect_url: URL to redirect to if usage exceeded.
                      If None, returns 403 Forbidden.

    Usage:
        @usage_within_limits()
        def api_view(request):
            return JsonResponse({"result": "ok"})

        @usage_within_limits(redirect_url='/upgrade/')
        def limited_view(request):
            return render(request, 'limited.html')

        # Combine with subscription_required
        @subscription_required()
        @usage_within_limits(redirect_url='/upgrade/')
        def premium_api(request):
            return JsonResponse({"data": "premium"})
    """

    def decorator(view_func: Callable):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                if redirect_url:
                    return redirect(redirect_url)
                return HttpResponseForbidden("Authentication required")

            try:
                external_id = get_external_id_for_user(user)
                client = get_lark_client()
                billing_state = client.customer_access.retrieve_billing_state(
                    external_id
                )

                if billing_state.has_overage_for_usage:
                    if redirect_url:
                        return redirect(redirect_url)
                    return HttpResponseForbidden("Usage limit exceeded")

            except lark.APIError:
                if redirect_url:
                    return redirect(redirect_url)
                return HttpResponseForbidden("Unable to verify usage limits")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def track_usage(
    event_name: str,
    data: Optional[Union[Dict[str, Union[str, int]], Callable]] = None,
    timestamp: Optional[Union[datetime, Callable]] = None,
    *,
    idempotency_key: Optional[Union[str, Callable]] = None,
    success_codes: Optional[List[int]] = None,
):
    """
    Decorator that tracks usage when a view returns a successful response.

    Records a usage event to Lark for metered billing when the decorated
    view returns a successful HTTP response (2xx by default).

    Args:
        event_name: The name of the usage event (must match pricing metric).
        data: Usage data dict or callable(request, response, *args, **kwargs)
              that returns the data dict. Defaults to {"count": 1}.
        timestamp: Timestamp of the usage event, or callable(request, response, *args, **kwargs)
                   that returns the timestamp. Defaults to current time.
        idempotency_key: Static key, or callable(request, response, *args, **kwargs)
                         that returns the key. Defaults to auto-generated UUID.
        success_codes: List of HTTP status codes to consider successful.
                       Defaults to 2xx range (200-299).

    Usage:
        # Simple - track each API call
        @track_usage("api_calls")
        def my_api_view(request):
            return JsonResponse({"result": "ok"})

        # With custom data
        @track_usage("api_calls", data={"count": 1, "endpoint": "users"})
        def users_api(request):
            return JsonResponse({"users": []})

        # Dynamic data based on response
        @track_usage(
            "tokens_used",
            data=lambda req, res, *a, **kw: {"tokens": res.get("tokens", 0)}
        )
        def llm_api(request):
            result = call_llm(request.POST["prompt"])
            return JsonResponse(result)

        # Custom idempotency key
        @track_usage(
            "file_uploads",
            idempotency_key=lambda req, res, *a, **kw: f"upload_{req.POST['file_id']}"
        )
        def upload_file(request):
            return JsonResponse({"status": "uploaded"})

    Note:
        - Only tracks usage for authenticated users
        - Silently fails if usage recording fails (doesn't break the view)
        - Uses the user's external_id to identify them in Lark
    """

    def decorator(view_func: Callable):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Execute the view first
            response = view_func(request, *args, **kwargs)

            # Check if we should track this response
            status_code = getattr(response, "status_code", 200)
            codes_to_track = success_codes or range(200, 300)

            if status_code not in codes_to_track:
                return response

            # Only track for authenticated users
            user = getattr(request, "user", None)
            if not user or not getattr(user, "is_authenticated", False):
                logger.error(f"User is not authenticated, skipping usage tracking")
                return response

            # Build usage data
            if callable(data):
                usage_data = data(request, response, *args, **kwargs)
            elif data is not None:
                usage_data = data
            else:
                usage_data = {}

            # Build timestamp
            if callable(timestamp):
                ts = timestamp(request, response, *args, **kwargs)
            elif timestamp is not None:
                ts = timestamp
            else:
                ts = datetime.now(timezone.utc)

            # Build idempotency key
            if callable(idempotency_key):
                key = idempotency_key(request, response, *args, **kwargs)
            elif idempotency_key is not None:
                key = idempotency_key
            else:
                key = str(uuid.uuid4())

            try:
                record_usage_for_user(
                    user,
                    event_name=event_name,
                    data=usage_data,
                    idempotency_key=key,
                    timestamp=ts,
                )
            except lark.APIError:
                logger.exception(f"Failed to record usage for user {user.id}")

            return response

        return wrapper

    return decorator
