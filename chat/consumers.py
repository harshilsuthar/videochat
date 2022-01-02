import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer

from .models.roomchat import Message, Room, RoomMember


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_number_id = self.scope['url_route']['kwargs']['room_number_id']
        self.room_group_name = 'chat_%s' % self.room_number_id

        # Join room group
        try:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
        except Exception as ex:
            print(ex)
        try:
            room_member = RoomMember.objects.get(room__room_number=self.room_number_id, member=self.scope['user'])
            room_member.is_online = True
            room_member.save()
        except Exception as ex:
            print(ex)
        online_room_member_names = list(RoomMember.objects.filter(room__room_number=self.room_number_id, is_online=True).values_list('member__first_name', flat=True))

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'new_user_join_signal',
                'room_number': str(room_member.room.room_number),
                'room_member_id': room_member.id,
                'online_room_member_names':online_room_member_names
            }
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        try:
            room_member = RoomMember.objects.get(room__room_number=self.room_number_id, member=self.scope['user'])
            room_member.is_online = False
            room_member.save()
        except Exception as ex:
            print(ex)

        online_room_member_names = list(RoomMember.objects.filter(room__room_number=self.room_number_id, is_online=True).values_list('member__first_name', flat=True))
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_user_offline_signal',
                    'room_number': str(room_member.room.room_number),
                    'room_member_id': room_member.id,
                    'online_room_member_names':online_room_member_names
                }
            )
        except Exception as ex:
            print(ex)

        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception as ex:
            print(ex)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        message_type = text_data_json.get('type')

        if message_type == 'chat_message':
            message = text_data_json.get('message')
            user_id = text_data_json.get('user_id')
            message = await self.create_message(message, self.room_number_id, user_id)

            # Send message to room group
            try:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message.message,
                        'message_id': message.id,
                        'room_member_id': message.room_member.id,
                        'room_member_image_src':message.room_member.member.image.url,
                        'room_member_first_name': message.room_member.member.first_name,
                        'user_id': message.room_member.member.id
                    }
                )
            except Exception as ex:
                print(ex)

        elif message_type == 'read_message_signal':
            room_number = text_data_json.get('room_number')
            user_id = text_data_json.get('user_id')
            try:
                room = Room.objects.get(room_number=room_number)
                room_member = RoomMember.objects.get(member__id=user_id, room=room)
                messages = [message.reader.add(room_member) for message in Message.objects.filter(room_member__room=room)]
            except Exception as ex:
                print(ex)

        elif message_type == 'invite_member':
            try:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        **text_data_json,
                        'sender': self.scope['user'].id
                    }
                )
            except Exception as ex:
                print(ex)
    # Receive message from room group

    async def chat_message(self, event):
        # Send message to WebSocket
        try:
            await self.send(text_data=json.dumps({
                **event
            }))
        except Exception as ex:
            print(ex)

    async def send_user_offline_signal(self, event):
        try:
            await self.send(text_data=json.dumps({
                **event
            }))
        except Exception as ex:
            print(ex)

    async def new_user_join_signal(self, event):
        try:
            await self.send(text_data=json.dumps({
                **event
            }))
        except Exception as ex:
            print(ex)

    async def file_upload(self, event):
        try:
            await self.send(text_data=json.dumps({
                **event
            }))
        except Exception as ex:
            print(ex)

    async def invite_member(self, event):
        try:
            await self.send(text_data=json.dumps({
                **event
            }))
        except Exception as ex:
            print(ex)

    @database_sync_to_async
    def create_message(self, message, room_number_id, user_id):
        try:
            room_member = RoomMember.objects.get(member__id=user_id, room__room_number=room_number_id)
            message = Message.objects.create(message=message, room_member=room_member)
            message.reader.add(room_member)
            return message
        except Exception as ex:
            print(ex)
            return False


class ProtectedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = 'protected_%s' % str(self.user_id)

        try:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
        except Exception as ex:
            print(ex)

        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'disconnect_success',
                    'room_group_name': self.room_group_name,
                }
            )
        except Exception as ex:
            print(ex)

    async def receive(self, text_data):
        text_data = json.loads(text_data)
        message_type = text_data['type']

        # new connection handler
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'connection_success',
                }
            )
        except Exception as ex:
            print(ex)

        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'update_discussion',
                }
            )
        except Exception as ex:
            print(ex)


    async def connection_success(self, event):
        try:
            await self.send(text_data=json.dumps({
                **event
            }))
        except Exception as ex:
            print(ex)

    async def update_discussion(self, event):
        try:
            await self.send(text_data=json.dumps({
                **event
            }))
        except Exception as ex:
            print(ex)
