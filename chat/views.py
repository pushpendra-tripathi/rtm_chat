from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin

from .forms import RoomForm  # Assuming you have a form for Room creation
from .models import Message, Room


class RoomListView(LoginRequiredMixin, FormMixin, ListView):
    model = Room
    template_name = "chat/index.html"
    context_object_name = "rooms"
    form_class = RoomForm  # Use the form for creating a Room

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.instance.creator = request.user  # Set the creator if needed
            form.save()
            return redirect("chat:index")  # Redirect to the room list after creation
        return self.form_invalid(form)


class RoomDetailView(LoginRequiredMixin, DetailView):
    model = Room
    template_name = "chat/room.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = self.get_object()
        context["messages"] = Message.objects.filter(room=room)[:100]
        return context
