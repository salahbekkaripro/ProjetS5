from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.plans_view, name="plans"),
    path("switch/<str:code>/", views.switch_plan, name="switch"),
    path("history/", views.subscription_history, name="history"),
]
