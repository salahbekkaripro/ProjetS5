from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'

    def ready(self):
        from django.db.models.signals import post_migrate

        from .signals import create_default_plans

        post_migrate.connect(create_default_plans, sender=self)
