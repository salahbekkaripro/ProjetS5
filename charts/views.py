import io
from datetime import timedelta
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from django.http import HttpResponse
from django.utils import timezone
from django.db import models

from subscriptions.decorators import requires_plan
from workouts.models import Workout, WorkoutSet, Exercise


@requires_plan("fitplus")
def volume_per_week(request):
    today = timezone.now().date()
    weeks = []
    volumes = []
    for i in range(4, -1, -1):
        start = today - timedelta(days=i * 7)
        end = start + timedelta(days=6)
        qs = Workout.objects.filter(user=request.user, date__range=(start, end))
        volume = sum(w.total_volume for w in qs)
        weeks.append(start.strftime("%d/%m"))
        volumes.append(volume)

    fig, ax = plt.subplots()
    ax.plot(weeks, volumes, marker="o")
    ax.set_title("Volume total / semaine")
    ax.set_ylabel("Volume (reps x poids)")
    ax.set_xlabel("Semaine")
    plt.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/png")


@requires_plan("fitplus")
def muscle_frequency(request):
    sets = (
        WorkoutSet.objects.filter(workout__user=request.user)
        .values_list("exercise__muscle_group", flat=True)
    )
    counter = Counter(sets)
    if not counter:
        counter["Aucune donnée"] = 1
    labels = list(counter.keys())
    values = list(counter.values())

    fig, ax = plt.subplots()
    bars = ax.bar(labels, values, color="#7cf7ff")
    ax.set_title("Fréquence par groupe musculaire")
    ax.set_ylabel("Sets")
    ax.bar_label(bars, padding=2)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/png")


@requires_plan("pro")
def one_rm_best(request):
    # estime par exercice (Epley) sur les 60 derniers jours
    since = timezone.now().date() - timedelta(days=60)
    records = (
        WorkoutSet.objects.filter(workout__user=request.user, workout__date__gte=since, reps__gt=0, weight__gt=0)
        .values("exercise")
        .annotate(
            est=models.ExpressionWrapper(
                models.F("weight") * (1 + models.F("reps") / 30.0),
                output_field=models.FloatField(),
            )
        )
        .annotate(best=models.Max("est"))
        .order_by("-best")[:5]
    )
    labels = []
    values = []
    exercise_map = {e.id: e.name for e in Exercise.objects.filter(id__in=[r["exercise"] for r in records])}
    for r in records:
        labels.append(exercise_map.get(r["exercise"], "Exercice"))
        values.append(float(r["best"]))
    if not values:
        labels, values = ["Pas de données"], [0]

    fig, ax = plt.subplots()
    bars = ax.barh(labels, values, color="#7f5af0")
    ax.invert_yaxis()
    ax.set_title("Meilleurs 1RM estimés (60j)")
    ax.set_xlabel("Kg (estimé)")
    ax.bar_label(bars, padding=3, fmt="%.1f")
    plt.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/png")
