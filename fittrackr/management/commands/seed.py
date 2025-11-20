from django.core.management.base import BaseCommand
from django.utils import timezone

from subscriptions.utils import ensure_default_plans
from shop.models import Category, Product
from workouts.models import Exercise
from workouts.utils import ensure_default_badges
from programs.models import Program, ProgramExercise


class Command(BaseCommand):
    help = "Seed default plans, categories, products, exercices, programmes, badges"

    def handle(self, *args, **options):
        ensure_default_plans()
        cat_names = ["T-shirts", "Accessoires", "Nutrition"]
        for name in cat_names:
            Category.objects.get_or_create(name=name)
        merch = [
            ("T-Shirt FitTrackR", "T-shirts", 24.99),
            ("Gourde Inox", "Accessoires", 14.99),
            ("Shaker", "Accessoires", 9.99),
            ("Barres protéinées", "Nutrition", 19.99),
        ]
        for name, cat_name, price in merch:
            category = Category.objects.get(name=cat_name)
            Product.objects.get_or_create(name=name, defaults={"category": category, "price": price, "stock": 100, "description": "Produit FitTrackR"})
        exercises = [
            ("Développé couché", "chest"),
            ("Squat", "legs"),
            ("Tractions", "back"),
            ("Planche", "core"),
        ]
        for name, muscle in exercises:
            Exercise.objects.get_or_create(name=name, muscle_group=muscle)
        ensure_default_badges()
        # Programmes prédéfinis
        full_body, _ = Program.objects.get_or_create(title="Full Body Débutant", defaults={"description": "3 jours", "program_type": "full_body", "is_predefined": True})
        pushpull, _ = Program.objects.get_or_create(title="PPL Classique", defaults={"description": "Push/Pull/Legs", "program_type": "ppl", "is_predefined": True})
        bench = Exercise.objects.filter(name="Développé couché").first()
        squat = Exercise.objects.filter(name="Squat").first()
        if bench:
            ProgramExercise.objects.get_or_create(program=full_body, exercise=bench, day=1, sets=3, reps=10, defaults={"notes": "Charge modérée"})
        if squat:
            ProgramExercise.objects.get_or_create(program=full_body, exercise=squat, day=2, sets=4, reps=8, defaults={"notes": "Progressif"})
        self.stdout.write(self.style.SUCCESS("Seed terminée."))
