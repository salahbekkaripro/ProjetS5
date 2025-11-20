import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from subscriptions.utils import ensure_default_plans
from subscriptions.models import Plan, Subscription
from users.models import CustomUser
from workouts.models import Exercise, Workout, WorkoutSet
from workouts.utils import ensure_default_badges
from shop.models import Category, Product, Order, OrderItem, MarketplaceListing


class Command(BaseCommand):
    help = "Generate demo data: test user, workouts over 30 days, orders, listings"

    def handle(self, *args, **options):
        ensure_default_plans()
        ensure_default_badges()

        user, created = CustomUser.objects.get_or_create(email="demo@fittrackr.test", defaults={"first_name": "Demo", "last_name": "User"})
        if created:
            user.set_password("demo1234")
            user.save()
            self.stdout.write(self.style.WARNING("User demo@fittrackr.test / demo1234 créé"))

        fitplus = Plan.objects.get(code="fitplus")
        Subscription.objects.update_or_create(user=user, defaults={"plan": fitplus, "active": True, "end_date": None})

        exercises_data = [
            ("Développé couché", "chest"),
            ("Squat", "legs"),
            ("Tractions", "back"),
            ("Développé militaire", "shoulders"),
            ("Soulevé de terre", "back"),
        ]
        exercises = []
        for name, muscle in exercises_data:
            ex, _ = Exercise.objects.get_or_create(name=name, muscle_group=muscle)
            exercises.append(ex)

        today = timezone.now().date()
        Workout.objects.filter(user=user, date__gte=today - timedelta(days=40)).delete()
        for i in range(20):
            day = today - timedelta(days=random.randint(0, 30))
            w = Workout.objects.create(
                user=user,
                title=f"Séance {i+1}",
                date=day,
                workout_type=random.choice(["strength", "cardio", "hiit"]),
            )
            sets_count = random.randint(3, 6)
            for s in range(sets_count):
                ex = random.choice(exercises)
                reps = random.choice([5, 8, 10, 12])
                weight = random.choice([40, 50, 60, 70, 80])
                WorkoutSet.objects.create(
                    workout=w,
                    exercise=ex,
                    set_number=s + 1,
                    reps=reps,
                    weight=weight,
                    notes="auto-demo",
                )

        cat, _ = Category.objects.get_or_create(name="Demo", defaults={"slug": "demo"})
        p1, _ = Product.objects.get_or_create(name="T-Shirt Demo", defaults={"category": cat, "price": 19.99, "stock": 50})
        p2, _ = Product.objects.get_or_create(name="Gourde Demo", defaults={"category": cat, "price": 12.99, "stock": 50})

        order, _ = Order.objects.get_or_create(user=user, email=user.email, full_name="Demo User", defaults={"address": "1 rue Demo", "city": "Paris", "paid": True})
        if not order.items.exists():
            OrderItem.objects.create(order=order, product=p1, quantity=1, price=p1.price)
            OrderItem.objects.create(order=order, product=p2, quantity=2, price=p2.price)

        listing, _ = MarketplaceListing.objects.get_or_create(seller=user, title="Chaussures Demo", defaults={"description": "Comme neuves", "price": 49.0, "condition": "good"})
        listing.available = True
        listing.save()

        self.stdout.write(self.style.SUCCESS("Données demo générées. Utilisateur: demo@fittrackr.test / demo1234"))
