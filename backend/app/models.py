from django.db import models
import uuid
import secrets
from datetime import timedelta

from django.utils import timezone

ROOM_RETENTION = timedelta(hours=1)
ROOM_MAX_LIFETIME = ROOM_RETENTION
ROOM_EXPIRY_WARNING = timedelta(minutes=5)


def generate_room_code():
    return uuid.uuid4().hex[:8].upper()


def generate_controller_token():
    return secrets.token_urlsafe(32)


def purge_expired_rooms(max_age=ROOM_RETENTION):
    cutoff = timezone.now() - max_age
    return ChatRoom.objects.filter(created_at__lt=cutoff).delete()


class ChatRoom(models.Model):
    code = models.CharField(
        max_length=8,
        unique=True,
        default=generate_room_code
    )

    controller_token = models.CharField(
        max_length=86,
        default=generate_controller_token,
        editable=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code