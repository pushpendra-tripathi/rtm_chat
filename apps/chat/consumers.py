import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Message, MessageReceipt, MessageStatus, Room


class ChatConsumer(AsyncWebsocketConsumer):
    # Store connected users and their room connections
    connected_users = {}

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope["user"]

        # Store user's connection
        if self.user.id not in self.connected_users:
            self.connected_users[self.user.id] = set()
        self.connected_users[self.user.id].add(self.room_id)

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Mark undelivered messages as delivered for this user in this room
        await self.mark_messages_as_delivered()

    async def disconnect(self, close_code):
        # Remove user's connection
        if self.user.id in self.connected_users:
            self.connected_users[self.user.id].discard(self.room_id)
            if not self.connected_users[self.user.id]:
                del self.connected_users[self.user.id]

        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def mark_messages_as_delivered(self):
        """Mark all undelivered messages as delivered when user connects"""
        room = Room.objects.get(id=self.room_id)
        # Get messages that are sent but not delivered/read
        undelivered_messages = Message.objects.filter(
            room=room,
            receipts__user=self.user,
            receipts__status=MessageStatus.SENT,
        ).exclude(sender=self.user)

        for message in undelivered_messages:
            message.mark_as_delivered(self.user)

    @database_sync_to_async
    def save_message(self, message):
        room = Room.objects.get(id=self.room_id)
        msg = Message.objects.create(room=room, sender=self.user, content=message)

        # Create MessageReceipt with SENT status for all other participants
        other_participants = room.participants.exclude(id=self.user.id)
        MessageReceipt.objects.bulk_create(
            [
                MessageReceipt(message=msg, user=participant, status=MessageStatus.SENT)
                for participant in other_participants
            ]
        )

        # Update to DELIVERED for online participants
        for participant in other_participants:
            if (
                participant.id in self.connected_users
                and self.room_id in self.connected_users[participant.id]
            ):
                msg.mark_as_delivered(participant)

        return msg

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "message")

        if message_type == "message":
            message = data["message"]
            saved_message = await self.save_message(message)

            # Broadcast message to room group
            message_data = {
                "type": "chat_message",
                "message": message,
                "message_id": saved_message.id,
                "sender_id": self.user.id,
                "sender_name": self.user.username,
                "timestamp": saved_message.dtm_created.isoformat(),
            }
            await self.channel_layer.group_send(self.room_group_name, message_data)

            # Send notification to all participants except sender
            room = await self.get_room()
            room_name = await self.get_room_name()
            notification_data = {
                "type": "notify_message",
                "room_id": self.room_id,
                "room_name": room_name,
                "message": message[:50] + "..." if len(message) > 50 else message,
                "sender_name": self.user.username,
                "timestamp": saved_message.dtm_created.isoformat(),
            }

            for participant in await self.get_participants():
                if participant.id != self.user.id:
                    await self.channel_layer.group_send(
                        f"notifications_{participant.id}", notification_data
                    )
        elif message_type == "status_update":
            message_id = data["message_id"]
            status = data["status"]

            # Update message status
            await self.update_message_status(message_id, status)

            # Broadcast status update
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "status_update",
                    "message_id": message_id,
                    "status": status,
                    "user_id": self.user.id,
                },
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def status_update(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def update_message_status(self, message_id, status):
        """Update message status for the current user"""
        try:
            message = Message.objects.get(id=message_id)
            # Only update status if the user is a recipient (not the sender)
            if message.sender != self.user:
                if status == MessageStatus.READ:
                    message.mark_as_read(self.user)
                elif status == MessageStatus.DELIVERED:
                    message.mark_as_delivered(self.user)
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def get_room(self):
        return Room.objects.get(id=self.room_id)

    @database_sync_to_async
    def get_room_name(self):
        """Get room name asynchronously"""
        room = Room.objects.get(id=self.room_id)
        return room.get_room_name()

    @database_sync_to_async
    def get_participants(self):
        """Get room participants asynchronously"""
        room = Room.objects.get(id=self.room_id)
        return list(room.participants.all())


class ChatNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.notification_group_name = f"notifications_{self.user.id}"

        # Join notification group
        await self.channel_layer.group_add(
            self.notification_group_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave notification group
        await self.channel_layer.group_discard(
            self.notification_group_name, self.channel_name
        )

    async def notify_message(self, event):
        """Send message notification to WebSocket"""
        await self.send(text_data=json.dumps(event))
