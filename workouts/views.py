from datetime import date, timedelta
import calendar
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from subscriptions.decorators import requires_plan
from subscriptions.utils import ensure_free_plan
from .forms import ExerciseForm, GoalForm, WorkoutFilterForm, WorkoutForm, WorkoutSetForm
from .models import Badge, Goal, Exercise, Workout, WorkoutSet
from .utils import check_and_award_badges, update_gamification


def _check_workout_limit(request_user):
    """Enforce workout weekly limit for free plan."""
    ensure_free_plan(request_user)
    sub = request_user.active_subscription
    if not sub:
        return False, "Aucun abonnement actif."
    plan = sub.plan
    if plan.workout_limit_per_week:
        today = timezone.now().date()
        start_week = today - timedelta(days=today.weekday())
        count = Workout.objects.filter(user=request_user, date__gte=start_week, date__lte=today).count()
        if count >= plan.workout_limit_per_week:
            return False, "Limite de workouts atteinte pour cette semaine (plan Free)."
    return True, None


@login_required
def workout_list(request):
    ensure_free_plan(request.user)
    today = timezone.now().date()
    try:
        month = int(request.GET.get("month", today.month))
        year = int(request.GET.get("year", today.year))
        if month < 1 or month > 12:
            raise ValueError
    except (TypeError, ValueError):
        month, year = today.month, today.year

    start_month = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_month = date(year, month, last_day)

    workouts = (
        Workout.objects.filter(user=request.user, date__gte=start_month, date__lte=end_month)
        .select_related()
        .prefetch_related("sets__exercise")
    )
    form = WorkoutFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data.get("date_from"):
            workouts = workouts.filter(date__gte=form.cleaned_data["date_from"])
        if form.cleaned_data.get("date_to"):
            workouts = workouts.filter(date__lte=form.cleaned_data["date_to"])
        if form.cleaned_data.get("muscle_group"):
            workouts = workouts.filter(sets__exercise__muscle_group=form.cleaned_data["muscle_group"])
        if form.cleaned_data.get("workout_type"):
            workouts = workouts.filter(workout_type=form.cleaned_data["workout_type"])
    workouts = workouts.distinct()

    workouts_by_day = {}
    for w in workouts:
        workouts_by_day.setdefault(w.date, []).append(w)

    cal = calendar.Calendar(firstweekday=0)
    raw_weeks = cal.monthdatescalendar(year, month)
    weeks_struct = []
    for week in raw_weeks:
        days = []
        for d in week:
            days.append(
                {
                    "date": d,
                    "in_month": d.month == month,
                    "workouts": workouts_by_day.get(d, []),
                }
            )
        weeks_struct.append(days)

    prev_month_date = (start_month - timedelta(days=1)).replace(day=1)
    next_month_date = (end_month + timedelta(days=1)).replace(day=1)

    context = {
        "workouts": workouts,
        "form": form,
        "weeks": weeks_struct,
        "current_month": month,
        "current_year": year,
        "current_label": start_month.strftime("%B %Y"),
        "prev_month": prev_month_date.month,
        "prev_year": prev_month_date.year,
        "next_month": next_month_date.month,
        "next_year": next_month_date.year,
    }
    return render(request, "workouts/workout_list.html", context)


@login_required
def workout_detail(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    set_form = WorkoutSetForm(request.POST or None)
    if request.method == "POST" and set_form.is_valid():
        workout_set = set_form.save(commit=False)
        workout_set.workout = workout
        # auto set number
        workout_set.set_number = WorkoutSet.objects.filter(workout=workout).count() + 1
        workout_set.save()
        check_and_award_badges(request.user)
        update_gamification(request.user, workout)
        messages.success(request, "Set ajouté.")
        return redirect("workouts:workout_detail", pk=pk)
    sets = workout.sets.select_related("exercise").all()
    return render(request, "workouts/workout_detail.html", {"workout": workout, "sets": sets, "set_form": set_form})


@requires_plan("pro")
def export_workout_pdf(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4 ratio
    ax.axis("off")
    y = 0.95
    ax.text(0.05, y, f"Workout : {workout.title}", fontsize=14, weight="bold")
    y -= 0.05
    ax.text(0.05, y, f"Date : {workout.date} | Type : {workout.get_workout_type_display()}")
    y -= 0.05
    for s in workout.sets.select_related("exercise").all():
        ax.text(
            0.05,
            y,
            f"Set {s.set_number} - {s.exercise.name} - Reps:{s.reps or '-'} Poids:{s.weight or '-'} Notes:{s.notes}",
            fontsize=10,
        )
        y -= 0.04
        if y < 0.05:
            break
    buffer = io.BytesIO()
    fig.savefig(buffer, format="pdf")
    plt.close(fig)
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="application/pdf")


@login_required
def workout_create(request):
    allowed, msg = _check_workout_limit(request.user)
    if not allowed:
        messages.warning(request, msg)
        return redirect("workouts:workout_list")
    if request.method == "POST":
        form = WorkoutForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)
            workout.user = request.user
            workout.save()
            check_and_award_badges(request.user)
            update_gamification(request.user, workout)
            messages.success(request, "Workout créé.")
            return redirect("workouts:workout_detail", pk=workout.pk)
    else:
        form = WorkoutForm()
    return render(request, "workouts/workout_form.html", {"form": form, "title": "Nouveau workout"})


@login_required
def workout_update(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == "POST":
        form = WorkoutForm(request.POST, instance=workout)
        if form.is_valid():
            form.save()
            messages.success(request, "Workout mis à jour.")
            return redirect("workouts:workout_detail", pk=pk)
    else:
        form = WorkoutForm(instance=workout)
    return render(request, "workouts/workout_form.html", {"form": form, "title": "Edition workout"})


@login_required
def workout_delete(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == "POST":
        workout.delete()
        messages.info(request, "Workout supprimé.")
        return redirect("workouts:workout_list")
    return render(request, "workouts/workout_confirm_delete.html", {"workout": workout})


@login_required
def exercise_list(request):
    exercises = Exercise.objects.all()
    return render(request, "workouts/exercise_list.html", {"exercises": exercises})


@login_required
def exercise_create(request):
    if request.method == "POST":
        form = ExerciseForm(request.POST)
        if form.is_valid():
            exercise = form.save(commit=False)
            exercise.created_by = request.user
            exercise.save()
            messages.success(request, "Exercice créé.")
            return redirect("workouts:exercise_list")
    else:
        form = ExerciseForm()
    return render(request, "workouts/exercise_form.html", {"form": form, "title": "Nouvel exercice"})


@login_required
def exercise_update(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    if request.method == "POST":
        form = ExerciseForm(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, "Exercice mis à jour.")
            return redirect("workouts:exercise_list")
    else:
        form = ExerciseForm(instance=exercise)
    return render(request, "workouts/exercise_form.html", {"form": form, "title": "Edition exercice"})


@login_required
def exercise_delete(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    if request.method == "POST":
        exercise.delete()
        messages.info(request, "Exercice supprimé.")
        return redirect("workouts:exercise_list")
    return render(request, "workouts/exercise_confirm_delete.html", {"exercise": exercise})


@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user)
    return render(request, "workouts/goal_list.html", {"goals": goals})


@login_required
def goal_create(request):
    if request.method == "POST":
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, "Objectif ajouté.")
            return redirect("workouts:goal_list")
    else:
        form = GoalForm()
    return render(request, "workouts/goal_form.html", {"form": form, "title": "Nouvel objectif"})


@login_required
def goal_update(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == "POST":
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            goal = form.save()
            if goal.progress_percent() >= 100 and not goal.achieved:
                goal.achieved = True
                goal.save(update_fields=["achieved"])
            messages.success(request, "Objectif mis à jour.")
            return redirect("workouts:goal_list")
    else:
        form = GoalForm(instance=goal)
    return render(request, "workouts/goal_form.html", {"form": form, "title": "Modifier l'objectif"})
