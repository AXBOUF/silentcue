import json 
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async

# tracks which channels are connected per room so we know when both peers are present
room_connections = {}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']

        self.room_group_name = f'chat_{self.room_id}'

        query_params = parse_qs(self.scope.get('query_string', b'').decode())
        self.role = query_params.get('role', ['user'])[0]
        controller_token = query_params.get('token', [''])[0]

        #VALIDATE THE ROOM EXISTS AND IS ACTIVE
        from .models import ChatRoom
        try:
            room = await database_sync_to_async(ChatRoom.objects.get)(code=self.room_id, is_active=True)
        except ChatRoom.DoesNotExist:
            await self.close()
            return
        if self.role == 'root' and controller_token != room.controller_token:
            await self.close()
            return
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        peers = room_connections.setdefault(self.room_id, set())
        peers.add(self.channel_name)
        if len(peers) == 2:
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'peer_status', 'connected': True}
            )

    async def disconnect(self, close_code):
        peers = room_connections.get(self.room_id)
        if peers:
            peers.discard(self.channel_name)
            if not peers:
                room_connections.pop(self.room_id, None)

        # only the room root leaving tears the room down; regular users can rejoin later
        if self.role == 'root':
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'room_dismantled'}
            )
        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'peer_status', 'connected': False}
            )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        if self.role == 'root':
            from .models import ChatRoom
            await database_sync_to_async(ChatRoom.objects.filter(code=self.room_id).delete)()

    async def receive(self, text_data):
        if self.role != 'root':
            return

        data = json.loads(text_data)
        value = data.get('value')
        if value not in ('next', 'back'):
            return

        name = (data.get('name') or '').strip() or ('Root' if self.role == 'root' else 'Guest')

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'signal',
                'value': value,
                'role': self.role,
                'name': name,
            }
        )

    async def signal(self, event):
        await self.send(text_data=json.dumps({
            'type': 'signal',
            'value': event['value'],
            'role': event['role'],
            'name': event['name'],
        }))

    async def peer_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'peer_status',
            'connected': event['connected'],
        }))

    async def room_dismantled(self, event):
        await self.send(text_data=json.dumps({
            'type': 'room_dismantled'
        }))


## the ChatConsumer class handles WebSocket connections for chat functionality.
    ## It accepts incoming WebSocket connections, sends a confirmation message upon connection,
    ## and can be extended to handle message reception and disconnection events.
    ## other applications of consumers include real-time notifications, live updates, and collaborative features.
