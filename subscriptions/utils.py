from django.db import transaction

from .models import PLAN_CODES, Plan, Subscription


DEFAULT_PLANS = [
    {"code": "free", "name": "Free", "level": 1, "price": 0, "description": "Plan gratuit avec limites", "workout_limit_per_week": 3, "features": "Workouts basiques"},
    {"code": "fitplus", "name": "Fit+", "level": 2, "price": 9.99, "description": "Graphiques et stats avancées", "features": "Graphiques d'évolution"},
    {"code": "pro", "name": "Pro", "level": 3, "price": 19.99, "description": "Exports PDF et outils avancés", "features": "Export PDF, stats détaillées"},
    {"code": "ultra", "name": "Ultra", "level": 4, "price": 29.99, "description": "Coaching IA illimité", "features": "Coaching IA, tout illimité"},
]


def ensure_default_plans():
    """Ensure the default plans exist."""
    for plan_data in DEFAULT_PLANS:
        Plan.objects.get_or_create(
            code=plan_data["code"],
            defaults={
                "name": plan_data["name"],
                "level": plan_data["level"],
                "price": plan_data["price"],
                "description": plan_data["description"],
                "workout_limit_per_week": plan_data.get("workout_limit_per_week"),
                "features": plan_data.get("features", ""),
            },
        )


def ensure_free_plan(user):
    """Assign the free plan to a user if they don't have any subscription."""
    ensure_default_plans()
    if Subscription.objects.filter(user=user, active=True).exists():
        return
    free_plan = Plan.objects.get(code="free")
    Subscription.objects.create(user=user, plan=free_plan)


def has_required_plan(user, code: str) -> bool:
    ensure_default_plans()
    if isinstance(code, str):
        try:
            required_plan = Plan.objects.get(code=code)
        except Plan.DoesNotExist:
            return False
    else:
        return False
    current = user.active_subscription
    return bool(current and current.plan.level >= required_plan.level and current.is_current)
