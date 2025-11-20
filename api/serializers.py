from rest_framework import serializers

from subscriptions.models import Plan
from workouts.models import Exercise, Workout, WorkoutSet
from shop.models import Product, MarketplaceListing
from programs.models import Program


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ["id", "name", "muscle_group", "equipment", "description"]


class WorkoutSetSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all(), source="exercise", write_only=True)

    class Meta:
        model = WorkoutSet
        fields = ["id", "set_number", "reps", "weight", "duration_seconds", "notes", "exercise", "exercise_id"]


class WorkoutSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True, required=False)

    class Meta:
        model = Workout
        fields = ["id", "title", "date", "workout_type", "notes", "total_volume", "sets"]
        read_only_fields = ["total_volume"]

    def create(self, validated_data):
        sets_data = validated_data.pop("sets", [])
        user = self.context["request"].user
        workout = Workout.objects.create(user=user, **validated_data)
        for idx, s in enumerate(sets_data, start=1):
            WorkoutSet.objects.create(workout=workout, set_number=idx, **s)
        return workout


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "stock", "category_id"]


class ListingSerializer(serializers.ModelSerializer):
    seller_email = serializers.EmailField(source="seller.email", read_only=True)

    class Meta:
        model = MarketplaceListing
        fields = ["id", "title", "description", "price", "condition", "available", "seller_email"]


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["code", "name", "price", "description", "level", "workout_limit_per_week", "features"]


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = ["id", "title", "description", "program_type", "level", "is_predefined"]
