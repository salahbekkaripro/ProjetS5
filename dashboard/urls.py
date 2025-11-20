from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("coach/", views.ai_coaching, name="ai_coaching"),
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("chat/", views.ai_chat, name="ai_chat"),
]
