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

    def get_room_name(self):
        """Sync method to get room name"""
        if self.chat_type == ChatType.PRIVATE:
            participants = list(self.participants.all())
            if len(participants) >= 2:
                return f"Chat between {participants[0]} and {participants[1]}"
        return self.name or f"Group {self.id}"

    def __str__(self):
        return self.get_room_name()


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def get_status_for_user(self, user):
        """Get the message status for a specific user"""
        try:
            receipt = self.receipts.get(user=user)
            return receipt.status
        except MessageReceipt.DoesNotExist:
            return MessageStatus.SENT

    def get_status_display(self):
        """Get overall message status for display"""
        if not self.receipts.exists():
            return MessageStatus.SENT

        statuses = list(self.receipts.values_list("status", flat=True))
        if all(status == MessageStatus.READ for status in statuses):
            return MessageStatus.READ
        if all(
            status in [MessageStatus.DELIVERED, MessageStatus.READ]
            for status in statuses
        ):
            return MessageStatus.DELIVERED
        return MessageStatus.SENT

    def mark_as_delivered(self, user):
        """Mark message as delivered for a user"""
        MessageReceipt.objects.update_or_create(
            message=self, user=user, defaults={"status": MessageStatus.DELIVERED}
        )

    def mark_as_read(self, user):
        """Mark message as read for a user"""
        MessageReceipt.objects.update_or_create(
            message=self, user=user, defaults={"status": MessageStatus.READ}
        )

    def create_receipts(self, exclude_user=None):
        """Create initial SENT receipts for all participants"""
        participants = self.room.participants.all()
        if exclude_user:
            participants = participants.exclude(id=exclude_user.id)

        MessageReceipt.objects.bulk_create(
            [
                MessageReceipt(
                    message=self, user=participant, status=MessageStatus.SENT
                )
                for participant in participants
            ]
        )


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
        get_latest_by = "timestamp"
