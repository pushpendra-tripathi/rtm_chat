import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Message, MessageReceipt, MessageStatus, Room


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("connect")
        print(self.scope["url_route"]["kwargs"])
        self.room_id = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope["user"]

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "message")

        if message_type == "message":
            message = data["message"]

            # Save message to database
            saved_message = await self.save_message(message)

            # Broadcast message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "message_id": saved_message.id,
                    "sender_id": self.user.id,
                    "timestamp": saved_message.created_at.isoformat(),
                },
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
    def save_message(self, message):
        room = Room.objects.get(id=self.room_id)
        msg = Message.objects.create(
            room=room, sender=self.user, content=message, status=MessageStatus.SENT
        )

        # Create delivered receipts for all other participants
        other_participants = room.participants.exclude(id=self.user.id)
        MessageReceipt.objects.bulk_create(
            [
                MessageReceipt(
                    message=msg, user=participant, status=MessageStatus.DELIVERED
                )
                for participant in other_participants
            ]
        )

        return msg

    @database_sync_to_async
    def update_message_status(self, message_id, status):
        MessageReceipt.objects.filter(message_id=message_id, user=self.user).update(
            status=status
        )
