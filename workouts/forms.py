from django import forms

from .models import GOAL_TYPES, MUSCLE_GROUPS, WORKOUT_TYPES, Exercise, Goal, Workout, WorkoutSet


class DateInput(forms.DateInput):
    input_type = "date"


class WorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        fields = ("title", "date", "workout_type", "notes")
        widgets = {"date": DateInput()}


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ("name", "muscle_group", "equipment", "description")


class WorkoutSetForm(forms.ModelForm):
    class Meta:
        model = WorkoutSet
        fields = ("exercise", "set_number", "reps", "weight", "duration_seconds", "notes")


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ("title", "goal_type", "exercise", "target_value", "deadline", "notes")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("goal_type") == "pr" and not cleaned.get("exercise"):
            self.add_error("exercise", "Choisissez un exercice pour un objectif PR.")
        return cleaned


class WorkoutFilterForm(forms.Form):
    date_from = forms.DateField(required=False, widget=DateInput())
    date_to = forms.DateField(required=False, widget=DateInput())
    muscle_group = forms.ChoiceField(required=False, choices=[("", "Tous les muscles")] + [(key, label) for key, label in MUSCLE_GROUPS])
    workout_type = forms.ChoiceField(required=False, choices=[("", "Tous les types")] + [(key, label) for key, label in WORKOUT_TYPES])
