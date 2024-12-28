from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Max, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from .forms import GroupChatForm, PrivateChatForm
from .models import Message, MessageReceipt, MessageStatus, Room


class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = "chat/index.html"
    context_object_name = "rooms"

    def get_queryset(self):
        return (
            Room.objects.filter(participants=self.request.user)
            .annotate(last_message_time=Max("messages__created_at"))
            .order_by("-last_message_time")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["private_chat_form"] = PrivateChatForm(user=self.request.user)
        context["group_chat_form"] = GroupChatForm(user=self.request.user)
        return context


class CreatePrivateChatView(LoginRequiredMixin, CreateView):
    model = Room
    form_class = PrivateChatForm
    success_url = reverse_lazy("chat:index")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class CreateGroupChatView(LoginRequiredMixin, CreateView):
    model = Room
    form_class = GroupChatForm
    success_url = reverse_lazy("chat:index")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class RoomDetailView(LoginRequiredMixin, DetailView):
    model = Room
    template_name = "chat/room.html"

    def get_object(self):
        room = super().get_object()
        if self.request.user not in room.participants.all():
            raise PermissionDenied
        return room

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = self.get_object()

        # Get messages with their receipts
        messages = (
            Message.objects.filter(room=room)
            .prefetch_related(
                Prefetch(
                    "receipts",
                    queryset=MessageReceipt.objects.filter(user=self.request.user),
                )
            )
            .order_by("-created_at")
        )

        # Mark messages as read
        unread_messages = messages.filter(
            sender=self.request.user,
            receipts__status__in=[MessageStatus.SENT, MessageStatus.DELIVERED],
        )[:100]

        for message in unread_messages:
            MessageReceipt.objects.update_or_create(
                message=message,
                user=self.request.user,
                defaults={"status": MessageStatus.READ},
            )

        context["messages"] = messages
        return context
