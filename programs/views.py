from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from subscriptions.decorators import requires_plan
from workouts.models import Exercise
from .forms import ProgramExerciseForm, ProgramForm
from .models import Program, ProgramAssignment, ProgramExercise


@login_required
def program_list(request):
    programs = Program.objects.all().prefetch_related("program_exercises__exercise")
    return render(request, "programs/program_list.html", {"programs": programs})


@login_required
def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)
    assignments = ProgramAssignment.objects.filter(user=request.user, program=program)
    return render(request, "programs/program_detail.html", {"program": program, "assignments": assignments})


@login_required
def assign_program(request, pk):
    program = get_object_or_404(Program, pk=pk)
    ProgramAssignment.objects.filter(user=request.user, active=True).update(active=False)
    ProgramAssignment.objects.create(user=request.user, program=program, active=True)
    messages.success(request, f"Programme {program.title} assigné.")
    return redirect("programs:my_programs")


@login_required
def my_programs(request):
    assignments = ProgramAssignment.objects.filter(user=request.user).select_related("program")
    return render(request, "programs/my_programs.html", {"assignments": assignments})


@requires_plan("pro")
def program_create(request):
    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save(commit=False)
            program.created_by = request.user
            program.save()
            messages.success(request, "Programme créé.")
            return redirect("programs:program_detail", pk=program.pk)
    else:
        form = ProgramForm()
    return render(request, "programs/program_form.html", {"form": form, "title": "Créer un programme"})


@requires_plan("pro")
def program_update(request, pk):
    program = get_object_or_404(Program, pk=pk, created_by=request.user)
    if request.method == "POST":
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, "Programme mis à jour.")
            return redirect("programs:program_detail", pk=pk)
    else:
        form = ProgramForm(instance=program)
    return render(request, "programs/program_form.html", {"form": form, "title": "Modifier le programme"})


@requires_plan("pro")
def add_program_exercise(request, pk):
    program = get_object_or_404(Program, pk=pk, created_by=request.user)
    if request.method == "POST":
        form = ProgramExerciseForm(request.POST)
        if form.is_valid():
            pe = form.save(commit=False)
            pe.program = program
            pe.save()
            messages.success(request, "Exercice ajouté au programme.")
            return redirect("programs:program_detail", pk=pk)
    else:
        form = ProgramExerciseForm()
    return render(request, "programs/program_exercise_form.html", {"form": form, "program": program})
