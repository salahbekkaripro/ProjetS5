from django.contrib import admin

from .models import Badge, Exercise, Goal, UserBadge, Workout, WorkoutSet, GamificationProfile


class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 0


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "date", "workout_type")
    list_filter = ("workout_type", "date")
    inlines = [WorkoutSetInline]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "muscle_group", "equipment")
    search_fields = ("name",)


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "goal_type", "target_value", "deadline", "achieved")
    list_filter = ("goal_type", "achieved")


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("title", "metric", "threshold")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_on")


@admin.register(GamificationProfile)
class GamificationProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "points", "streak_current", "streak_best", "last_workout_date")
