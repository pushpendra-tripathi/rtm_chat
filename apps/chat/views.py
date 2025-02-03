from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Max, Prefetch, Q
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
            .annotate(
                last_message_time=Max("messages__dtm_created"),
                unread_count=Count(
                    "messages",
                    filter=Q(
                        messages__receipts__user=self.request.user,
                        messages__receipts__status=MessageStatus.SENT,
                    ),
                ),
                participant_count=Count("participants", distinct=True),
            )
            .prefetch_related(
                Prefetch(
                    "messages",
                    queryset=Message.objects.order_by("-dtm_created"),
                    to_attr="recent_messages",
                ),
                "participants",
            )
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

        # Get messages with their receipts, ordered by dtm_created ascending
        messages = (
            Message.objects.filter(room=room)
            .prefetch_related(
                Prefetch(
                    "receipts",
                    queryset=MessageReceipt.objects.filter(user=self.request.user),
                )
            )
            .order_by("dtm_created")[:100]
        )

        # Get all chat rooms for the sidebar
        chat_rooms = (
            Room.objects.filter(participants=self.request.user)
            .annotate(last_message_time=Max("messages__dtm_created"))
            .order_by("-last_message_time")
        )

        context.update(
            {
                "messages": messages,
                "chat_rooms": chat_rooms,
                "private_chat_form": PrivateChatForm(user=self.request.user),
                "group_chat_form": GroupChatForm(user=self.request.user),
            }
        )
        return context
