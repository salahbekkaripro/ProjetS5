from django.conf import settings
from django.db import models

from workouts.models import Exercise

PROGRAM_TYPES = [
    ("full_body", "Full Body"),
    ("ppl", "Push/Pull/Legs"),
    ("split", "Split"),
    ("custom", "Personnalisé"),
]


class Program(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPES, default="full_body")
    level = models.CharField(max_length=50, default="Tous")
    is_predefined = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_predefined", "title"]

    def __str__(self):
        return self.title


class ProgramExercise(models.Model):
    program = models.ForeignKey(Program, related_name="program_exercises", on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    day = models.PositiveIntegerField(default=1)
    sets = models.PositiveIntegerField(default=3)
    reps = models.PositiveIntegerField(default=10)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["day", "id"]

    def __str__(self):
        return f"{self.program.title} - Day {self.day} - {self.exercise.name}"


class ProgramAssignment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="program_assignments", on_delete=models.CASCADE)
    program = models.ForeignKey(Program, related_name="assignments", on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]
        unique_together = ("user", "program", "active")

    def __str__(self):
        return f"{self.user.email} -> {self.program.title}"
