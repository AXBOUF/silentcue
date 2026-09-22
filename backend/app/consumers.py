import asyncio
import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import ChatRoom, ROOM_EXPIRY_WARNING, ROOM_MAX_LIFETIME

SESSION_CHECK_INTERVAL = 30
HEARTBEAT_TIMEOUT = 90

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
        try:
            room = await database_sync_to_async(ChatRoom.objects.get)(
                code=self.room_id,
                is_active=True,
                created_at__gte=timezone.now() - ROOM_MAX_LIFETIME,
            )
        except ChatRoom.DoesNotExist:
            await self.close()
            return
        if self.role == 'root' and controller_token != room.controller_token:
            await self.close()
            return
        self.room_created_at = room.created_at
        self.last_signal_at = timezone.now()
        self.last_heartbeat_at = timezone.now()
        self.expiry_warning_sent = False
        self.expiration_task = None
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        self.expiration_task = asyncio.create_task(self.monitor_session())

        peers = room_connections.setdefault(self.room_id, set())
        peers.add(self.channel_name)
        if len(peers) == 2:
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'peer_status', 'connected': True}
            )

    async def disconnect(self, close_code):
        if self.expiration_task:
            self.expiration_task.cancel()
            self.expiration_task = None

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
            await database_sync_to_async(ChatRoom.objects.filter(code=self.room_id).delete)()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'heartbeat':
            self.last_heartbeat_at = timezone.now()
            await self.send(text_data=json.dumps({'type': 'heartbeat_ack'}))
            return

        if self.role != 'root':
            return

        value = data.get('value')
        if value not in (0, 1):
            return

        name = (data.get('name') or '').strip() or ('Root' if self.role == 'root' else 'Guest')
        self.last_signal_at = timezone.now()

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
            'type': 'room_dismantled',
            'reason': event.get('reason', 'controller_left'),
        }))
        await self.close(code=4001)

    async def session_warning(self, event):
        await self.send(text_data=json.dumps({
            'type': 'session_warning',
            'remaining_seconds': event['remaining_seconds'],
        }))

    async def monitor_session(self):
        try:
            while True:
                await asyncio.sleep(SESSION_CHECK_INTERVAL)
                now = timezone.now()
                age = now - self.room_created_at
                idle_for = now - self.last_signal_at
                heartbeat_age = now - self.last_heartbeat_at

                if age >= ROOM_MAX_LIFETIME:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {'type': 'room_dismantled', 'reason': 'expired'},
                    )
                    return

                if heartbeat_age.total_seconds() >= HEARTBEAT_TIMEOUT:
                    await self.close(code=4002)
                    return

                if idle_for >= ROOM_MAX_LIFETIME:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {'type': 'room_dismantled', 'reason': 'idle_timeout'},
                    )
                    return

                remaining = ROOM_MAX_LIFETIME - age
                if remaining <= ROOM_EXPIRY_WARNING and not self.expiry_warning_sent:
                    self.expiry_warning_sent = True
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'session_warning',
                            'remaining_seconds': max(0, int(remaining.total_seconds())),
                        },
                    )
        except asyncio.CancelledError:
            return


## the ChatConsumer class handles WebSocket connections for chat functionality.
    ## It accepts incoming WebSocket connections, sends a confirmation message upon connection,
    ## and can be extended to handle message reception and disconnection events.
    ## other applications of consumers include real-time notifications, live updates, and collaborative features.
