from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import FriendRequestForm, MessageForm
from .models import FriendRequest, Friendship, Message

User = get_user_model()


def _friends(user):
    return Friendship.friends_for(user)


@login_required
def inbox(request):
    friends = _friends(request.user)
    incoming_requests = FriendRequest.objects.filter(receiver=request.user, status=FriendRequest.Status.PENDING)
    sent_requests = FriendRequest.objects.filter(sender=request.user, status=FriendRequest.Status.PENDING)
    recent_messages = (
        Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
        .order_by("-created_at")[:10]
        .select_related("sender", "receiver")
    )
    friend_form = FriendRequestForm()
    return render(
        request,
        "messaging/inbox.html",
        {
            "friends": friends,
            "incoming_requests": incoming_requests,
            "sent_requests": sent_requests,
            "recent_messages": recent_messages,
            "friend_form": friend_form,
        },
    )


@login_required
def conversation(request, user_id):
    other = get_object_or_404(User, pk=user_id)
    if other == request.user:
        messages.info(request, "Ceci est votre propre profil.")
    if other not in _friends(request.user) and other != request.user:
        messages.error(request, "Vous devez être amis pour discuter.")
        return redirect("messaging:inbox")

    thread_messages = Message.conversation_between(request.user, other).select_related("sender", "receiver")
    Message.objects.filter(receiver=request.user, sender=other, is_read=False).update(is_read=True)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(sender=request.user, receiver=other, body=form.cleaned_data["body"])
            messages.success(request, "Message envoyé.")
            return redirect("messaging:conversation", user_id=other.id)
    else:
        form = MessageForm()

    return render(
        request,
        "messaging/conversation.html",
        {"other": other, "thread_messages": thread_messages, "form": form},
    )


@login_required
def send_friend_request(request):
    if request.method != "POST":
        return redirect("messaging:inbox")

    form = FriendRequestForm(request.POST)
    if not form.is_valid():
        messages.error(request, " ".join(form.errors.get("__all__", [])) or form.errors.as_text())
        return redirect("messaging:inbox")

    user_to_add = form.cleaned_data["user_obj"]
    if user_to_add == request.user:
        messages.error(request, "Vous ne pouvez pas vous ajouter vous-même.")
        return redirect("messaging:inbox")

    if user_to_add in _friends(request.user):
        messages.info(request, "Vous êtes déjà amis.")
        return redirect("messaging:conversation", user_id=user_to_add.id)

    existing_inverse = FriendRequest.objects.filter(
        sender=user_to_add, receiver=request.user, status=FriendRequest.Status.PENDING
    ).first()
    if existing_inverse:
        existing_inverse.accept()
        messages.success(request, f"Vous avez accepté automatiquement la demande de {user_to_add.email}.")
        return redirect("messaging:conversation", user_id=user_to_add.id)

    fr, created = FriendRequest.objects.get_or_create(sender=request.user, receiver=user_to_add)
    if created:
        messages.success(request, f"Demande envoyée à {user_to_add.email}.")
    else:
        if fr.status == FriendRequest.Status.PENDING:
            messages.info(request, "Une demande est déjà en attente.")
        elif fr.status == FriendRequest.Status.ACCEPTED:
            messages.info(request, "Vous êtes déjà amis.")
        else:
            fr.status = FriendRequest.Status.PENDING
            fr.save(update_fields=["status"])
            messages.success(request, f"Demande renvoyée à {user_to_add.email}.")

    return redirect("messaging:inbox")


@login_required
def accept_friend_request(request, pk):
    fr = get_object_or_404(FriendRequest, pk=pk, receiver=request.user, status=FriendRequest.Status.PENDING)
    with transaction.atomic():
        fr.accept()
    messages.success(request, f"Vous êtes maintenant ami avec {fr.sender.email}.")
    return redirect("messaging:inbox")


@login_required
def decline_friend_request(request, pk):
    fr = get_object_or_404(FriendRequest, pk=pk, receiver=request.user, status=FriendRequest.Status.PENDING)
    fr.decline()
    messages.info(request, "Demande refusée.")
    return redirect("messaging:inbox")
