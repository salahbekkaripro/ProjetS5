from django.contrib import admin

from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "level", "price", "workout_limit_per_week")
    prepopulated_fields = {"code": ("name",)}
    ordering = ("level",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "start_date", "end_date", "active")
    list_filter = ("plan__code", "active")
    search_fields = ("user__email",)
