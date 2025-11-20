from django.urls import path

from . import views

app_name = "workouts"

urlpatterns = [
    path("", views.workout_list, name="workout_list"),
    path("create/", views.workout_create, name="workout_create"),
    path("<int:pk>/", views.workout_detail, name="workout_detail"),
    path("<int:pk>/edit/", views.workout_update, name="workout_update"),
    path("<int:pk>/delete/", views.workout_delete, name="workout_delete"),
    path("<int:pk>/export/", views.export_workout_pdf, name="workout_export"),
    path("exercises/", views.exercise_list, name="exercise_list"),
    path("exercises/create/", views.exercise_create, name="exercise_create"),
    path("exercises/<int:pk>/edit/", views.exercise_update, name="exercise_update"),
    path("exercises/<int:pk>/delete/", views.exercise_delete, name="exercise_delete"),
    path("goals/", views.goal_list, name="goal_list"),
    path("goals/create/", views.goal_create, name="goal_create"),
    path("goals/<int:pk>/edit/", views.goal_update, name="goal_update"),
]
