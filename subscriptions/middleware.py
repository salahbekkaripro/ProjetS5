from .models import Subscription
from .utils import ensure_free_plan


class SubscriptionMiddleware:
    """Attach the active subscription to the request for convenience."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_subscription = None
        if request.user.is_authenticated:
            ensure_free_plan(request.user)
            request.current_subscription = (
                Subscription.objects.select_related("plan")
                .filter(user=request.user, active=True)
                .order_by("-start_date")
                .first()
            )
        response = self.get_response(request)
        return response
