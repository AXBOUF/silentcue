from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import ChatRoom, ROOM_RETENTION, purge_expired_rooms


class RoomRetentionTests(TestCase):
	def test_purge_expired_rooms_removes_rooms_older_than_one_hour(self):
		expired_room = ChatRoom.objects.create(code="EXPIRED1")
		active_room = ChatRoom.objects.create(code="ACTIVE01")
		old_timestamp = timezone.now() - ROOM_RETENTION - timedelta(seconds=1)
		ChatRoom.objects.filter(pk=expired_room.pk).update(created_at=old_timestamp)

		purge_expired_rooms()

		self.assertFalse(ChatRoom.objects.filter(pk=expired_room.pk).exists())
		self.assertTrue(ChatRoom.objects.filter(pk=active_room.pk).exists())
