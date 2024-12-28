from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ChatType(models.TextChoices):
    PRIVATE = "private", _("Private Chat")
    GROUP = "group", _("Group Chat")


class MessageStatus(models.TextChoices):
    SENT = "sent", _("Sent")
    DELIVERED = "delivered", _("Delivered")
    READ = "read", _("Read")


class Room(models.Model):
    name = models.CharField(max_length=255, blank=True)
    chat_type = models.CharField(
        max_length=20, choices=ChatType.choices, default=ChatType.PRIVATE
    )
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_rooms"
    )
    participants = models.ManyToManyField(User, related_name="rooms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.chat_type == ChatType.PRIVATE:
            participants = self.participants.all()
            return f"Chat between {participants[0]} and {participants[1]}"
        return self.name


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField()
    status = models.CharField(
        max_length=20, choices=MessageStatus.choices, default=MessageStatus.SENT
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class MessageReceipt(models.Model):
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="receipts"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="message_receipts"
    )
    status = models.CharField(
        max_length=20, choices=MessageStatus.choices, default=MessageStatus.DELIVERED
    )
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["message", "user"]
