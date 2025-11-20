from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class FriendRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_friend_requests")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_friend_requests")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("sender", "receiver")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.sender} -> {self.receiver} ({self.status})"

    def accept(self) -> None:
        Friendship.create_pair(self.sender, self.receiver)
        self.status = self.Status.ACCEPTED
        self.save(update_fields=["status"])

    def decline(self) -> None:
        self.status = self.Status.DECLINED
        self.save(update_fields=["status"])


class Friendship(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friendships_initiated")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friendships_received")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user1", "user2"], name="unique_friendship_pair"),
            models.CheckConstraint(check=~Q(user1=models.F("user2")), name="friendship_distinct_users"),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # enforce ordering to keep uniqueness symmetrical
        if self.user1_id and self.user2_id and self.user1_id > self.user2_id:
            self.user1, self.user2 = self.user2, self.user1
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.user1} ⇄ {self.user2}"

    @staticmethod
    def create_pair(user_a, user_b):
        if user_a.id > user_b.id:
            user_a, user_b = user_b, user_a
        friendship, _ = Friendship.objects.get_or_create(user1=user_a, user2=user_b)
        return friendship

    @staticmethod
    def friends_for(user):
        qs = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        return [f.user2 if f.user1 == user else f.user1 for f in qs]


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Message from {self.sender} to {self.receiver}"

    @staticmethod
    def conversation_between(user_a, user_b):
        return Message.objects.filter(
            Q(sender=user_a, receiver=user_b) | Q(sender=user_b, receiver=user_a)
        ).order_by("created_at")
