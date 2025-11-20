"""
Petit module ML pour FitTrackR.
- Détection de surentraînement via IsolationForest (non supervisé) si assez d'historique.
- Estimation de tendance 1RM via régression linéaire sur les derniers sets.
Si les données sont insuffisantes, on retombe sur des règles heuristiques.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from django.db import models
from django.utils import timezone

from .models import Exercise, Workout, WorkoutSet


def _safe_import_sklearn():
    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.linear_model import LinearRegression

        return IsolationForest, LinearRegression
    except Exception:
        return None, None


def weekly_features(user) -> List[Dict]:
    """Aggregate workouts by week."""
    today = timezone.now().date()
    start = today - timedelta(days=90)
    workouts = (
        Workout.objects.filter(user=user, date__gte=start)
        .prefetch_related("sets__exercise")
        .order_by("date")
    )
    weeks = defaultdict(lambda: {"volume": 0, "sessions": 0, "avg_reps": 0, "set_count": 0})
    for w in workouts:
        year, week_num, _ = w.date.isocalendar()
        key = f"{year}-{week_num}"
        data = weeks[key]
        data["sessions"] += 1
        for s in w.sets.all():
            data["volume"] += s.volume
            if s.reps:
                data["avg_reps"] += s.reps
                data["set_count"] += 1
    # finalize averages
    result = []
    for key, v in sorted(weeks.items()):
        avg_reps = v["avg_reps"] / v["set_count"] if v["set_count"] else 0
        result.append({"week": key, "volume": v["volume"], "sessions": v["sessions"], "avg_reps": avg_reps})
    return result


def overtraining_risk(user) -> Dict[str, Optional[float]]:
    """
    Retourne un score de risque basé sur IsolationForest.
    Si données insuffisantes (<4 semaines), renvoie None + heuristique.
    """
    IsolationForest, _ = _safe_import_sklearn()
    data = weekly_features(user)
    if len(data) < 4 or not IsolationForest:
        # heuristique simple : comparer volume semaine N vs N-1
        if len(data) >= 2:
            last, prev = data[-1], data[-2]
            ratio = (last["volume"] or 1) / (prev["volume"] or 1)
            risk = 0.7 if ratio > 1.6 and last["sessions"] >= 5 else 0.3
            return {"risk": risk, "reason": "Heuristique (données limitées)", "ratio": ratio}
        return {"risk": None, "reason": "Pas assez de données", "ratio": None}

    X = [[d["volume"], d["sessions"], d["avg_reps"]] for d in data]
    model = IsolationForest(n_estimators=100, contamination=0.2, random_state=42)
    try:
        model.fit(X)
        scores = model.decision_function(X)
    except Exception:
        # fallback si fit échoue
        if len(data) >= 2:
            last, prev = data[-1], data[-2]
            ratio = (last["volume"] or 1) / (prev["volume"] or 1)
            risk = 0.7 if ratio > 1.6 and last["sessions"] >= 5 else 0.3
            return {"risk": risk, "reason": "Heuristique (fallback ML)", "ratio": ratio}
        return {"risk": None, "reason": "Erreur modèle", "ratio": None}
    # plus le score est bas, plus c'est anormal; on mappe à un risque 0-1
    last_score = scores[-1]
    # scale roughly: score typique proche de 0; valeurs négatives = risque
    risk = float(min(1, max(0, 0.5 - last_score)))
    return {"risk": risk, "reason": "IsolationForest (90j)", "ratio": None}


def estimate_1rm_trend(user, exercise: Exercise) -> Optional[Tuple[float, float, float]]:
    """
    Estime la tendance 1RM (poids estimé) sur les 60 derniers jours via régression.
    Retourne (current_best, predicted_next, slope) ou None si données insuffisantes.
    """
    _, LinearRegression = _safe_import_sklearn()
    since = timezone.now().date() - timedelta(days=60)
    qs = (
        WorkoutSet.objects.filter(workout__user=user, workout__date__gte=since, exercise=exercise, reps__gt=0, weight__gt=0)
        .annotate(
            est=models.ExpressionWrapper(
                models.F("weight") * (1 + models.F("reps") / 30.0),
                output_field=models.FloatField(),
            )
        )
        .order_by("workout__date")
    )
    points = list(qs.values_list("workout__date", "est"))
    if len(points) < 3 or not LinearRegression:
        return None
    # encode dates as ordinal for regression
    X = [[p[0].toordinal()] for p in points]
    y = [float(p[1]) for p in points]
    reg = LinearRegression()
    reg.fit(X, y)
    current_best = max(y)
    next_date = timezone.now().date() + timedelta(days=7)
    predicted = float(reg.predict([[next_date.toordinal()]])[0])
    slope = float(reg.coef_[0])
    return current_best, predicted, slope
