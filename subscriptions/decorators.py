from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from .utils import has_required_plan


def requires_plan(code):
    """Decorator that checks the user's plan level."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('users:login')}?next={request.path}")
            if has_required_plan(request.user, code):
                return view_func(request, *args, **kwargs)
            messages.warning(request, "Cette page nécessite un abonnement supérieur.")
            return redirect("subscriptions:plans")

        return _wrapped

    return decorator
