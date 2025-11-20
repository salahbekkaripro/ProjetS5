from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("conversation/<int:user_id>/", views.conversation, name="conversation"),
    path("friend-request/send/", views.send_friend_request, name="send_friend_request"),
    path("friend-request/<int:pk>/accept/", views.accept_friend_request, name="accept_friend_request"),
    path("friend-request/<int:pk>/decline/", views.decline_friend_request, name="decline_friend_request"),
]
