"""
URL configuration for fittrackr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api import views as api_views

router = routers.DefaultRouter()
router.register("workouts", api_views.WorkoutViewSet, basename="workout")
router.register("exercises", api_views.ExerciseViewSet, basename="exercise")
router.register("products", api_views.ProductViewSet, basename="product")
router.register("listings", api_views.MarketplaceListingViewSet, basename="listing")
router.register("plans", api_views.PlanViewSet, basename="plan")
router.register("programs", api_views.ProgramViewSet, basename="program")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("workouts/", include("workouts.urls")),
    path("programs/", include("programs.urls")),
    path("subscriptions/", include("subscriptions.urls")),
    path("shop/", include("shop.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("charts/", include("charts.urls")),
    path("messaging/", include("messaging.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include(router.urls)),
    path("", RedirectView.as_view(pattern_name="dashboard:home", permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
