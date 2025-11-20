from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from subscriptions.utils import ensure_free_plan
from .forms import CustomUserCreationForm, UserUpdateForm


def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            ensure_free_plan(user)
            login(request, user)
            messages.success(request, "Bienvenue sur FitTrackR !")
            return redirect("dashboard:home")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})


@login_required
def profile_view(request):
    subscription = getattr(request, "current_subscription", None)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect("users:profile")
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, "users/profile.html", {"form": form, "subscription": subscription})


def logout_view(request):
    logout(request)
    messages.info(request, "Déconnecté.")
    return redirect("users:login")
