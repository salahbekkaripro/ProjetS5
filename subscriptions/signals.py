from django.db.models.signals import post_migrate

from .utils import ensure_default_plans


def create_default_plans(sender, **kwargs):
    ensure_default_plans()
