from django.conf import settings
from django.db import models
from django.utils import timezone

WORKOUT_TYPES = [
    ("strength", "Force"),
    ("cardio", "Cardio"),
    ("hiit", "HIIT"),
    ("mobility", "Mobilité"),
]

MUSCLE_GROUPS = [
    ("full_body", "Full body"),
    ("chest", "Pectoraux"),
    ("back", "Dos"),
    ("legs", "Jambes"),
    ("shoulders", "Epaules"),
    ("arms", "Bras"),
    ("core", "Core"),
    ("cardio", "Cardio"),
]


class Exercise(models.Model):
    name = models.CharField(max_length=120)
    muscle_group = models.CharField(max_length=50, choices=MUSCLE_GROUPS)
    equipment = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "muscle_group")

    def __str__(self) -> str:
        return self.name


class Workout(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workouts")
    title = models.CharField(max_length=150)
    date = models.DateField(default=timezone.now)
    workout_type = models.CharField(max_length=20, choices=WORKOUT_TYPES, default="strength")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.title} - {self.date}"

    @property
    def total_volume(self):
        return sum(s.volume for s in self.sets.all())


class WorkoutSet(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="sets")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="sets")
    set_number = models.PositiveIntegerField(default=1)
    reps = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["workout", "set_number"]

    def __str__(self) -> str:
        return f"{self.workout} - {self.exercise} - Set {self.set_number}"

    @property
    def volume(self):
        if self.reps and self.weight:
            return float(self.reps) * float(self.weight)
        return 0

    @property
    def estimated_1rm(self):
        if self.reps and self.weight:
            # Epley formula
            return float(self.weight) * (1 + (self.reps / 30))
        return None


class GamificationProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gamification")
    points = models.PositiveIntegerField(default=0)
    streak_current = models.PositiveIntegerField(default=0)
    streak_best = models.PositiveIntegerField(default=0)
    last_workout_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Gamification {self.user.email}"

    @property
    def level(self):
        # simple level: every 100 pts
        return (self.points // 100) + 1


GOAL_TYPES = [
    ("pr", "Record personnel (1RM)"),
    ("sessions", "Nombre de séances"),
]


class Goal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=150)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    exercise = models.ForeignKey(Exercise, on_delete=models.SET_NULL, null=True, blank=True)
    target_value = models.DecimalField(max_digits=8, decimal_places=2)
    deadline = models.DateField(null=True, blank=True)
    achieved = models.BooleanField(default=False)
    achieved_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["achieved", "deadline", "-created_at"]

    def __str__(self):
        return self.title

    def current_value(self):
        from django.db.models import Max

        if self.goal_type == "sessions":
            return Workout.objects.filter(user=self.user).count()
        if self.goal_type == "pr" and self.exercise:
            best = (
                WorkoutSet.objects.filter(workout__user=self.user, exercise=self.exercise)
                .annotate(est= models.ExpressionWrapper(models.F("weight") * (1 + models.F("reps") / 30.0), output_field=models.FloatField()))
                .aggregate(Max("est"))
            )["est__max"]
            return best or 0
        return 0

    def progress_percent(self):
        current = float(self.current_value() or 0)
        target = float(self.target_value)
        if target == 0:
            return 0
        return min(100, round((current / target) * 100, 1))


BADGE_METRICS = [
    ("workouts", "Nombre de workouts"),
    ("volume", "Volume total"),
]


class Badge(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    metric = models.CharField(max_length=20, choices=BADGE_METRICS)
    threshold = models.PositiveIntegerField()

    class Meta:
        ordering = ["threshold"]

    def __str__(self):
        return self.title


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="user_badges", on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, related_name="assignments", on_delete=models.CASCADE)
    awarded_on = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "badge")
        ordering = ["-awarded_on"]

    def __str__(self):
        return f"{self.user.email} - {self.badge.title}"
