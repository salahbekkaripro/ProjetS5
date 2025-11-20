from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import EmailAuthenticationForm
from . import views

app_name = "users"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="users/login.html", authentication_form=EmailAuthenticationForm), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("profile/", views.profile_view, name="profile"),
]
