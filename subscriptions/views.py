from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Plan, Subscription
from .utils import ensure_default_plans


@login_required
def plans_view(request):
    ensure_default_plans()
    plans = Plan.objects.all()
    current = request.current_subscription
    return render(request, "subscriptions/plans.html", {"plans": plans, "current": current})


@login_required
def switch_plan(request, code):
    ensure_default_plans()
    plan = get_object_or_404(Plan, code=code)
    current = request.current_subscription
    if current and current.plan_id == plan.id and current.is_current:
        messages.info(request, "Vous êtes déjà sur ce plan.")
        return redirect("subscriptions:plans")
    if current and current.active:
        current.deactivate()
    Subscription.objects.create(user=request.user, plan=plan)
    messages.success(request, f"Votre abonnement a été mis à jour vers {plan.name}.")
    return redirect("subscriptions:plans")


@login_required
def subscription_history(request):
    subs = (
        Subscription.objects.filter(user=request.user)
        .select_related("plan")
        .order_by("-created_at", "-start_date")
    )
    return render(request, "subscriptions/history.html", {"subscriptions": subs})
