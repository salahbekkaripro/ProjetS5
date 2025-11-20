from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from .models import Badge, GamificationProfile, UserBadge, Workout, WorkoutSet


DEFAULT_BADGES = [
    ("starter", "Départ", "5 workouts au compteur", "workouts", 5),
    ("steady", "Constante", "20 workouts complétés", "workouts", 20),
    ("volume_10k", "Volume 10k", "10 000 de volume cumulé", "volume", 10000),
]


def ensure_default_badges():
    for code, title, desc, metric, threshold in DEFAULT_BADGES:
        Badge.objects.get_or_create(code=code, defaults={"title": title, "description": desc, "metric": metric, "threshold": threshold})


def _user_metric(user, metric):
    if metric == "workouts":
        return Workout.objects.filter(user=user).count()
    if metric == "volume":
        return WorkoutSet.objects.filter(workout__user=user).aggregate(total=Sum("reps"))["total"] or 0
    return 0


def check_and_award_badges(user):
    ensure_default_badges()
    owned_codes = set(UserBadge.objects.filter(user=user).values_list("badge__code", flat=True))
    for badge in Badge.objects.all():
        if badge.code in owned_codes:
            continue
        if _user_metric(user, badge.metric) >= badge.threshold:
            UserBadge.objects.create(user=user, badge=badge)


def get_or_create_gamification(user) -> GamificationProfile:
    profile, _ = GamificationProfile.objects.get_or_create(user=user)
    return profile


def update_gamification(user, workout: Workout | None = None):
    profile = get_or_create_gamification(user)
    points_gain = 0
    if workout:
        points_gain += 10  # base per workout
        points_gain += workout.sets.count() * 2
        today = workout.date
        if profile.last_workout_date:
            delta = today - profile.last_workout_date
            if delta == timedelta(days=1):
                profile.streak_current += 1
            elif delta == timedelta(0):
                # same day, do not change streak but still allow points
                pass
            else:
                profile.streak_current = 1
        else:
            profile.streak_current = 1
        profile.last_workout_date = today
        profile.streak_best = max(profile.streak_best, profile.streak_current)
    profile.points += points_gain
    profile.save()
    return profile
