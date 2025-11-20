from django.core.management.base import BaseCommand

from subscriptions.utils import ensure_default_plans
from shop.models import Category, Product
from workouts.models import Exercise


class Command(BaseCommand):
    help = "Seed default plans, categories, products, and exercises"

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
            Product.objects.get_or_create(
                name=name,
                defaults={"category": category, "price": price, "stock": 100, "description": "Produit FitTrackR"},
            )
        exercises = [
            ("Développé couché", "chest"),
            ("Squat", "legs"),
            ("Tractions", "back"),
            ("Planche", "core"),
        ]
        for name, muscle in exercises:
            Exercise.objects.get_or_create(name=name, muscle_group=muscle)
        self.stdout.write(self.style.SUCCESS("Seed terminée."))
