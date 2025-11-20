from django import forms

from workouts.models import Exercise
from .models import Program, ProgramAssignment, ProgramExercise


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ("title", "description", "program_type", "level", "is_predefined")


class ProgramExerciseForm(forms.ModelForm):
    class Meta:
        model = ProgramExercise
        fields = ("exercise", "day", "sets", "reps", "notes")


class ProgramAssignmentForm(forms.ModelForm):
    class Meta:
        model = ProgramAssignment
        fields = ()
