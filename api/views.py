from rest_framework import permissions, viewsets

from programs.models import Program
from shop.models import MarketplaceListing, Product
from subscriptions.models import Plan
from workouts.models import Exercise, Workout
from .serializers import ExerciseSerializer, ListingSerializer, PlanSerializer, ProductSerializer, ProgramSerializer, WorkoutSerializer


class BaseUserQuerysetMixin:
    """Restrict queryset to current user when the model has a user field."""

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(qs.model, "user"):
            return qs.filter(user=self.request.user)
        return qs


class WorkoutViewSet(BaseUserQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = WorkoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Workout.objects.all().prefetch_related("sets__exercise")


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Exercise.objects.all()


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.filter(is_active=True)


class MarketplaceListingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = MarketplaceListing.objects.filter(available=True)


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Plan.objects.all()


class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProgramSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Program.objects.all()
