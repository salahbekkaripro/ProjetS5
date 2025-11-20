from django.contrib import admin

from .models import Program, ProgramAssignment, ProgramExercise


class ProgramExerciseInline(admin.TabularInline):
    model = ProgramExercise
    extra = 0


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "program_type", "level", "is_predefined")
    inlines = [ProgramExerciseInline]


@admin.register(ProgramAssignment)
class ProgramAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "program", "start_date", "active")
    list_filter = ("active",)
