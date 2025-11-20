"""Assistant IA FitTrackR : intents + analytics (1RM, surentraînement, reco exos)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import re
from typing import Dict, List, Optional, Sequence, Tuple

from django.db.models import Count
from django.utils import timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from workouts.ml import estimate_1rm_trend, overtraining_risk
from workouts.models import Exercise, Workout, WorkoutSet, MUSCLE_GROUPS


@dataclass
class IntentPattern:
    label: str
    examples: Sequence[str]


@dataclass
class OneRMInsight:
    exercise: str
    current: float
    predicted: float
    slope: float


@dataclass
class UserInsights:
    workouts_30d: int
    volume_30d: float
    favorite_muscle: Optional[str]
    weak_muscle: Optional[str]
    plan_name: Optional[str]
    overtraining: Dict[str, Optional[float]]
    one_rm: List[OneRMInsight]
    user_name: Optional[str]


@dataclass
class ChatResponse:
    text: str
    intent: str
    confidence: float
    metadata: Dict[str, str] = field(default_factory=dict)


MUSCLE_LABELS = {code: label for code, label in MUSCLE_GROUPS}

INTENT_PATTERNS: List[IntentPattern] = [
    IntentPattern("greeting", ["bonjour", "salut", "hello", "yo", "merci", "ça va"]),
    IntentPattern("one_rm", ["1rm", "maxi", "progression force", "mon max", "developpe couche record", "squat 1rm", "rm progression", "force tendance"]),
    IntentPattern("fatigue", ["surentrainement", "fatigué", "récupération", "repos", "fatigue", "courbatures", "je suis crevé", "rpe haut"]),
    IntentPattern("recommendations", ["programme", "recommandation", "que travailler", "push pull legs", "exos pour moi", "muscle faible", "plan", "cycle"]),
    IntentPattern("stats", ["statistiques", "bilan", "résumé", "derniers entraînements", "volume", "progression globale", "graphique"]),
    IntentPattern("identity", ["je m'appelle", "mon nom", "appelle moi", "je suis", "retient mon nom"]),
]

KEYWORD_OVERRIDES = {
    "1rm": "one_rm",
    "max": "one_rm",
    "fatigue": "fatigue",
    "surentrain": "fatigue",
    "repos": "fatigue",
    "programme": "recommendations",
    "exercice": "recommendations",
    "stat": "stats",
    "m'appel": "identity",
    "appelle moi": "identity",
    "prenom": "identity",
    "prénom": "identity",
    "mon nom": "identity",
}

_SAMPLES: List[str] = []
_SAMPLE_LABELS: List[str] = []
for pattern in INTENT_PATTERNS:
    for sample in pattern.examples:
        _SAMPLES.append(sample.lower())
        _SAMPLE_LABELS.append(pattern.label)

_VECTORIZER = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), lowercase=True)
_TFIDF_MATRIX = _VECTORIZER.fit_transform(_SAMPLES)


def _format_muscle(code: Optional[str]) -> Optional[str]:
    if code is None:
        return None
    return MUSCLE_LABELS.get(code, code)


def _extract_name(message: str) -> Optional[str]:
    msg = message.strip()
    match = re.search(r"m[' ]?appelle\s+([A-Za-zÀ-ÖØ-öø-ÿ'-]+)", msg, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip().replace("'", " ")
    match_alt = re.search(r"appelle moi\s+([A-Za-zÀ-ÖØ-öø-ÿ'-]+)", msg, flags=re.IGNORECASE)
    if match_alt:
        return match_alt.group(1).strip().replace("'", " ")
    return None


def detect_intent(message: str) -> Tuple[str, float]:
    """Classe la requête dans un intent via similarité n-gram + mots-clés."""
    if not message:
        return "fallback", 0.0
    msg = message.lower()
    vec = _VECTORIZER.transform([msg])
    sims = cosine_similarity(vec, _TFIDF_MATRIX).flatten()
    if sims.size == 0:
        return "fallback", 0.0
    idx = sims.argmax()
    score = float(sims[idx])
    label = _SAMPLE_LABELS[idx]
    for keyword, override_label in KEYWORD_OVERRIDES.items():
        if keyword in msg:
            return override_label, max(score, 0.6)
    if score < 0.18:
        return "fallback", score
    return label, score


def _one_rm_insights(user) -> List[OneRMInsight]:
    """Retourne jusqu'à 3 tendances 1RM basées sur les exos les plus utilisés."""
    since = timezone.now().date() - timedelta(days=60)
    top_exercises = (
        WorkoutSet.objects.filter(workout__user=user, workout__date__gte=since, reps__gt=0, weight__gt=0)
        .values("exercise")
        .annotate(c=Count("id"))
        .order_by("-c")
        .values_list("exercise", flat=True)[:5]
    )
    insights: List[OneRMInsight] = []
    for ex_id in top_exercises:
        exercise = Exercise.objects.filter(id=ex_id).first()
        if not exercise:
            continue
        res = estimate_1rm_trend(user, exercise)
        if not res:
            continue
        current, predicted, slope = res
        insights.append(
            OneRMInsight(
                exercise=exercise.name,
                current=round(current, 1),
                predicted=round(predicted, 1),
                slope=round(slope * 7, 3),  # slope/semaine approximative
            )
        )
        if len(insights) >= 3:
            break
    return insights


def collect_insights(user, plan_name: Optional[str] = None, stored_name: Optional[str] = None) -> UserInsights:
    """Calcule les stats nécessaires au chatbot (sur 30-60 jours)."""
    today = timezone.now().date()
    last_month = today - timedelta(days=30)
    workouts_30d = Workout.objects.filter(user=user, date__gte=last_month).count()
    sets_30d = WorkoutSet.objects.filter(workout__user=user, workout__date__gte=last_month)
    volume_30d = sum(s.volume for s in sets_30d)
    muscles = list(
        sets_30d.values("exercise__muscle_group")
        .annotate(c=Count("id"))
        .order_by("-c")
    )
    favorite = muscles[0]["exercise__muscle_group"] if muscles else None
    weak = muscles[-1]["exercise__muscle_group"] if len(muscles) > 1 else None
    overtraining = overtraining_risk(user)
    one_rm = _one_rm_insights(user)
    return UserInsights(
        workouts_30d=workouts_30d,
        volume_30d=float(volume_30d),
        favorite_muscle=favorite,
        weak_muscle=weak if weak != favorite else None,
        plan_name=plan_name,
        overtraining=overtraining,
        one_rm=one_rm,
        user_name=stored_name or getattr(user, "first_name", None) or getattr(user, "username", None),
    )


def _recommended_exercises(weak_muscle: Optional[str], limit: int = 3) -> List[str]:
    if not weak_muscle:
        return []
    return [ex.name for ex in Exercise.objects.filter(muscle_group=weak_muscle).order_by("name")[:limit]]


def _handle_greeting(_: str, insights: UserInsights) -> str:
    prefix = f"Salut {insights.user_name} !" if insights.user_name else "Salut !"
    parts = [
        f"{prefix} Tu as enregistré {insights.workouts_30d} séances sur 30 jours pour ~{int(insights.volume_30d)} reps/volume total.",
    ]
    if insights.plan_name:
        parts.append(f"Abonnement actuel : {insights.plan_name}.")
    if insights.favorite_muscle:
        parts.append(f"Muscle dominant : {_format_muscle(insights.favorite_muscle)}.")
    if insights.weak_muscle:
        parts.append(f"Muscle à rattraper : {_format_muscle(insights.weak_muscle)} (je peux proposer des exos ciblés).")
    parts.append("Je peux analyser ton 1RM, le risque de surentraînement ou te proposer un focus d'exercices.")
    return " ".join(parts)


def _handle_stats(_: str, insights: UserInsights) -> str:
    parts = [
        f"Bilan 30j : {insights.workouts_30d} séances, ~{int(insights.volume_30d)} reps/volume.",
    ]
    if insights.favorite_muscle:
        parts.append(f"Muscle le plus travaillé : {_format_muscle(insights.favorite_muscle)}.")
    if insights.overtraining.get("risk") is not None:
        risk_pct = round(float(insights.overtraining["risk"]) * 100)
        parts.append(f"Risque de surentraînement estimé : {risk_pct}% ({insights.overtraining.get('reason')}).")
    if insights.plan_name:
        parts.append(f"Plan : {insights.plan_name}.")
    if insights.one_rm:
        best = insights.one_rm[0]
        parts.append(f"1RM estimé le plus récent : {best.exercise} ≈ {best.current} kg.")
    parts.append("Besoin d'un focus précis ? Demande-moi ton 1RM, ton risque fatigue ou un plan d'exos.")
    return " ".join(parts)


def _handle_one_rm(_: str, insights: UserInsights) -> str:
    if not insights.one_rm:
        return "Pas assez de séries chargées récentes pour estimer un 1RM. Logge 3 séances avec reps + poids (60 derniers jours) et je calcule ta tendance."
    details = []
    for entry in insights.one_rm:
        trend = f"{entry.predicted} kg prévus si tu maintiens le rythme" if entry.predicted else "pas de projection"
        speed = f"{entry.slope:+.3f} kg/semaine" if entry.slope else "tendance stable"
        details.append(f"{entry.exercise} : {entry.current} kg estimés, {speed}, {trend}.")
    tips = "Conserve un RPE 7-8 et ajoute 1-2 singles techniques pour sécuriser la progression."
    return " ".join(details + [tips])


def _handle_fatigue(_: str, insights: UserInsights) -> str:
    risk = insights.overtraining.get("risk")
    reason = insights.overtraining.get("reason") or "Analyse 90j"
    if risk is None:
        return "Pas assez de recul pour détecter un surentraînement. Logge au moins 4 semaines d'entraînements pour une détection fiable."
    risk_pct = round(float(risk) * 100)
    if risk_pct >= 70:
        advice = "Allège le volume de 20-30% cette semaine, garde 2 jours de repos, et dors 8h. Surveille les douleurs."
    elif risk_pct >= 40:
        advice = "Risque modéré : reste en RPE 7, ajoute un jour léger (mobilité/cardio), et limite les sets à échec."
    else:
        advice = "Risque faible : continue ta progression en surveillant le sommeil et l'hydratation."
    return f"Risque de surentraînement : {risk_pct}% ({reason}). {advice}"


def _handle_recommendations(_: str, insights: UserInsights) -> str:
    muscle = _format_muscle(insights.weak_muscle) if insights.weak_muscle else None
    recos = _recommended_exercises(insights.weak_muscle)
    if muscle and recos:
        return (
            f"Muscle à renforcer : {muscle}. Ajoute {', '.join(recos)} 2x/sem, en 3-4 séries contrôlées."
            " Termine par un tempo lent ou un iso pour sécuriser la technique."
        )
    if insights.favorite_muscle:
        return f"Ton volume est surtout sur {_format_muscle(insights.favorite_muscle)}. Pour équilibrer, ajoute 1 séance axée sur jambes/dos/épaules selon ton besoin, et reste en RPE 7."
    return "Je peux te proposer des exercices dès que tu auras loggé plusieurs séances avec des groupes musculaires variés."


def _handle_fallback(_: str, insights: UserInsights) -> str:
    base = [
        "Je m'appuie sur tes données FitTrackR (1RM, fatigue, muscles forts/faibles).",
        f"Sur 30 jours : {insights.workouts_30d} séances, ~{int(insights.volume_30d)} reps/volume.",
    ]
    base.append("Pose une question du style : \"mon 1rm bench ?\", \"je suis fatigué\", \"que travailler cette semaine ?\" ou \"bilan stats\".")
    return " ".join(base)


def _handle_identity(message: str, insights: UserInsights) -> str:
    name = _extract_name(message) or insights.user_name
    if name:
        return f"Enchanté {name}, je le note et je l'utiliserai dans nos échanges."
    return "Je veux bien retenir ton prénom : dis-moi \"je m'appelle <ton prénom>\"."


HANDLERS = {
    "greeting": _handle_greeting,
    "one_rm": _handle_one_rm,
    "fatigue": _handle_fatigue,
    "recommendations": _handle_recommendations,
    "stats": _handle_stats,
    "fallback": _handle_fallback,
    "identity": _handle_identity,
}


def generate_chat_reply(user, message: str, plan_name: Optional[str] = None, stored_name: Optional[str] = None) -> ChatResponse:
    insights = collect_insights(user, plan_name=plan_name, stored_name=stored_name)
    if stored_name:
        insights.user_name = stored_name
    intent, score = detect_intent(message)
    handler = HANDLERS.get(intent, _handle_fallback)
    text = handler(message, insights)
    metadata: Dict[str, str] = {}
    if intent == "identity":
        extracted = _extract_name(message)
        if extracted:
            metadata["remember_name"] = extracted
    if intent == "fallback" or (score < 0.22 and intent != "identity"):
        text += " Je ne suis pas sûr d'avoir compris : tu veux parler de 1RM, fatigue ou recommandations d'exos ?"
    return ChatResponse(text=text, intent=intent, confidence=score, metadata=metadata)
