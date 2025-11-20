from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


PLAN_CODES = [
    ("free", "Free"),
    ("fitplus", "Fit+"),
    ("pro", "Pro"),
    ("ultra", "Ultra"),
]


class Plan(models.Model):
    code = models.CharField(max_length=20, unique=True, choices=PLAN_CODES)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    level = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    workout_limit_per_week = models.PositiveIntegerField(null=True, blank=True)
    features = models.TextField(blank=True)

    class Meta:
        ordering = ["level"]

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def level_for_code(code: str) -> int:
        order = getattr(settings, "SUBSCRIPTION_PLAN_ORDER", [])
        if code in order:
            return order.index(code) + 1
        return 0


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="subscriptions")
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(fields=["user"], condition=Q(active=True), name="unique_active_subscription")
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.plan.name}"

    @property
    def is_current(self) -> bool:
        today = timezone.now().date()
        return self.active and (self.end_date is None or self.end_date >= today)

    def deactivate(self):
        self.active = False
        self.end_date = self.end_date or timezone.now().date()
        self.save(update_fields=["active", "end_date"])
