from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from subscriptions.decorators import requires_plan
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from shop.models import Order, Product, MarketplaceListing
from subscriptions.models import Subscription
from users.models import CustomUser
from workouts.models import Exercise, Goal, Workout, WorkoutSet
from workouts.utils import check_and_award_badges
from workouts.ml import overtraining_risk, estimate_1rm_trend
from workouts.utils import get_or_create_gamification
from dashboard.models import ChatMemory
from django.views.decorators.http import require_http_methods
from .ai_engine import generate_chat_reply


@login_required
def home(request):
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    prev_week_start = last_week - timedelta(days=7)
    workouts = Workout.objects.filter(user=request.user).prefetch_related("sets__exercise")[:5]
    workouts_count = Workout.objects.filter(user=request.user, date__gte=last_week).count()
    volume_week = WorkoutSet.objects.filter(workout__user=request.user, workout__date__gte=last_week).aggregate(
        total=Sum("reps")
    )["total"] or 0
    volume_prev = (
        WorkoutSet.objects.filter(workout__user=request.user, workout__date__gte=prev_week_start, workout__date__lt=last_week)
        .aggregate(total=Sum("reps"))
        .get("total")
        or 0
    )
    risk_info = overtraining_risk(request.user)
    overtraining_flag = bool(risk_info.get("risk") and risk_info["risk"] > 0.6)
    recommendations = (
        WorkoutSet.objects.filter(workout__user=request.user, workout__date__gte=today - timedelta(days=30))
        .values("exercise__muscle_group")
        .annotate(count=Count("id"))
        .order_by("count")[:3]
    )
    check_and_award_badges(request.user)
    muscle_stats = list(
        WorkoutSet.objects.filter(workout__user=request.user)
        .values("exercise__muscle_group")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    strengths = muscle_stats[:2]
    weaknesses = list(reversed(muscle_stats))[:2] if muscle_stats else []
    subscription = getattr(request, "current_subscription", None)
    badges = request.user.user_badges.select_related("badge")
    goals = Goal.objects.filter(user=request.user, achieved=False)
    # tendances 1RM sur les exos clés
    key_exercises = Exercise.objects.filter(name__in=["Squat", "Développé couché", "Tractions"])[:3]
    trends = []
    for ex in key_exercises:
        res = estimate_1rm_trend(request.user, ex)
        if res:
            trends.append({"exercise": ex.name, "current": round(res[0], 1), "pred": round(res[1], 1), "slope": round(res[2], 3)})
    gamification = get_or_create_gamification(request.user)

    context = {
        "workouts": workouts,
        "workouts_count": workouts_count,
        "volume_week": volume_week,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "subscription": subscription,
        "badges": badges,
        "goals": goals,
        "overtraining_flag": overtraining_flag,
        "risk_info": risk_info,
        "volume_prev": volume_prev,
        "recommendations": recommendations,
        "trends": trends,
        "gamification": gamification,
    }
    return render(request, "dashboard/home.html", context)


@requires_plan("ultra")
def ai_coaching(request):
    tips = [
        "Augmente progressivement le volume sur tes exercices clés.",
        "Priorise la récupération : sommeil et mobilité légère.",
        "Varie les tempi pour stimuler l'hypertrophie.",
    ]
    return render(request, "dashboard/ai_coaching.html", {"tips": tips})


@staff_member_required
def admin_dashboard(request):
    user_count = CustomUser.objects.count()
    active_subs = Subscription.objects.filter(active=True).count()
    orders_count = Order.objects.count()
    revenue = sum(o.total for o in Order.objects.all())
    products_count = Product.objects.count()
    listings_open = MarketplaceListing.objects.filter(available=True).count()
    data = {
        "user_count": user_count,
        "active_subs": active_subs,
        "orders_count": orders_count,
        "revenue": revenue,
        "products_count": products_count,
        "listings_open": listings_open,
    }
    latest_users = CustomUser.objects.order_by("-date_joined")[:5]
    recent_orders = Order.objects.order_by("-created_at")[:5]
    return render(request, "dashboard/admin_dashboard.html", {"stats": data, "latest_users": latest_users, "recent_orders": recent_orders})


@login_required
@require_http_methods(["GET", "POST"])
def ai_chat(request):
    """
    Chatbot IA analytique (1RM, surentraînement, reco exos) avec données locales.
    Historique conservé en session (limité à 10 messages).
    """
    history = request.session.get("ai_chat_history", [])
    stored_name = request.session.get("ai_user_name")
    response = None
    if request.method == "POST":
        user_msg = request.POST.get("message", "").strip()
        if user_msg:
            plan = getattr(request, "current_subscription", None)
            plan_name = plan.plan.name if plan else None
            reply = generate_chat_reply(request.user, user_msg, plan_name=plan_name, stored_name=stored_name)
            response = reply.text
            if reply.metadata.get("remember_name"):
                stored_name = reply.metadata["remember_name"]
                request.session["ai_user_name"] = stored_name
            ChatMemory.objects.create(user=request.user, question=user_msg, answer=response)
            history.append({"role": "user", "text": user_msg})
            history.append(
                {
                    "role": "assistant",
                    "text": response,
                    "intent": reply.intent,
                    "score": round(reply.confidence, 2),
                }
            )
            history = history[-10:]
            request.session["ai_chat_history"] = history
    return render(request, "dashboard/ai_chat.html", {"history": history, "response": response})
