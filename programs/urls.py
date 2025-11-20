from django.urls import path

from . import views

app_name = "programs"

urlpatterns = [
    path("", views.program_list, name="program_list"),
    path("mine/", views.my_programs, name="my_programs"),
    path("<int:pk>/", views.program_detail, name="program_detail"),
    path("<int:pk>/assign/", views.assign_program, name="assign_program"),
    path("create/", views.program_create, name="program_create"),
    path("<int:pk>/edit/", views.program_update, name="program_update"),
    path("<int:pk>/add-exercise/", views.add_program_exercise, name="add_program_exercise"),
]
