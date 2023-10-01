import json

# from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from chat.models.roomchat import RoomMember

# from channels.layers import channel_layers


consumer_count = {}


class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("\n\n-----------connected\n\n\n\n")
        self.room_number = self.scope["url_route"]["kwargs"]["room_number"]
        self.room_group_name = "call_%s" % str(self.room_number)
        try:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        except Exception as ex:
            print(ex)

        await self.accept()
        global consumer_count
        if self.room_number in consumer_count.keys():
            consumer_count[self.room_number] += 1
        else:
            consumer_count[self.room_number] = 1
        print(consumer_count, "------consumer count")

    async def disconnect(self, close_code):
        try:
            global consumer_count
            consumer_count[self.room_number] -= 1
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "closing_signal",
                    "localUuid": self.room_number
                    + "-"
                    + str(
                        RoomMember.objects.get(
                            room__room_number=self.room_number,
                            member=self.scope["user"],
                        ).id
                    ),
                },
            )
        except Exception as ex:
            print(ex)
        except Exception as ex:
            print(ex)

    async def receive(self, text_data):
        text_data = json.loads(text_data)
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {**text_data, "current_user_id": self.scope["user"].id},
            )
        except Exception as ex:
            print(ex)

    async def start_call(self, event):
        try:
            await self.send(text_data=json.dumps({**event}))
        except Exception as ex:
            print(ex)

    async def closing_signal(self, event):
        try:
            await self.send(text_data=json.dumps({**event}))
        except Exception as ex:
            print(ex)
