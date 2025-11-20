from django.urls import path

from . import views

app_name = "charts"

urlpatterns = [
    path("volume/", views.volume_per_week, name="volume_per_week"),
    path("muscle-frequency/", views.muscle_frequency, name="muscle_frequency"),
    path("one-rm/", views.one_rm_best, name="one_rm_best"),
]
