from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.RoomListView.as_view(), name="index"),
    path("room/<int:pk>/", views.RoomDetailView.as_view(), name="room_detail"),
]
