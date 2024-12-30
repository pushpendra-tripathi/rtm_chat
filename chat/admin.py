from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Message, MessageReceipt, MessageStatus, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = [
        "name_display",
        "chat_type",
        "creator",
        "participant_count",
        "message_count",
        "created_at",
    ]
    list_filter = ["chat_type", "created_at"]
    search_fields = ["name", "creator__username", "participants__username"]
    readonly_fields = ["created_at", "updated_at"]
    filter_horizontal = ["participants"]
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                message_count=Count("messages", distinct=True),
                participant_count=Count("participants", distinct=True),
            )
        )

    def name_display(self, obj):
        return str(obj)

    name_display.short_description = "Name"

    def participant_count(self, obj):
        return obj.participant_count

    participant_count.short_description = "Participants"
    participant_count.admin_order_field = "participant_count"

    def message_count(self, obj):
        return obj.message_count

    message_count.short_description = "Messages"
    message_count.admin_order_field = "message_count"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "truncated_content",
        "room_display",
        "sender",
        "status_display",
        "created_at",
    ]
    list_filter = ["created_at", "room__chat_type"]
    search_fields = ["content", "sender__username", "room__name"]
    readonly_fields = ["created_at", "status_display"]
    date_hierarchy = "created_at"
    raw_id_fields = ["room", "sender"]

    def truncated_content(self, obj):
        return (obj.content[:50] + "...") if len(obj.content) > 50 else obj.content

    truncated_content.short_description = "Content"

    def room_display(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            f"/admin/chat/room/{obj.room.id}/change/",
            str(obj.room),
        )

    room_display.short_description = "Room"
    room_display.admin_order_field = "room"

    def status_display(self, obj):
        status = obj.get_status_display()
        status_colors = {
            MessageStatus.READ: "blue",
            MessageStatus.DELIVERED: "green",
            MessageStatus.SENT: "gray",
        }
        return format_html(
            '<span style="color: {}">{}</span>',
            status_colors.get(status, "black"),
            obj.get_status_display(),
        )

    status_display.short_description = "Status"


@admin.register(MessageReceipt)
class MessageReceiptAdmin(admin.ModelAdmin):
    list_display = ["id", "message_display", "user", "status", "timestamp"]
    list_filter = ["status", "timestamp"]
    search_fields = ["message__content", "user__username", "message__room__name"]
    readonly_fields = ["timestamp"]
    date_hierarchy = "timestamp"
    raw_id_fields = ["message", "user"]

    def message_display(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            f"/admin/chat/message/{obj.message.id}/change/",
            obj.message.content[:50] + ("..." if len(obj.message.content) > 50 else ""),
        )

    message_display.short_description = "Message"
    message_display.admin_order_field = "message"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("message", "user", "message__room")
        )


# Optional: Register custom admin site
class ChatAdminSite(admin.AdminSite):
    site_header = "Chat Administration"
    site_title = "Chat Admin Portal"
    index_title = "Chat Management"


# Uncomment below lines if you want a separate admin site for chat
# chat_admin_site = ChatAdminSite(name='chat_admin')
# chat_admin_site.register(Room, RoomAdmin)
# chat_admin_site.register(Message, MessageAdmin)
# chat_admin_site.register(MessageReceipt, MessageReceiptAdmin)
