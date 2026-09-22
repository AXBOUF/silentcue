from django.core.management.base import BaseCommand

from app.models import purge_expired_rooms


class Command(BaseCommand):
    help = 'Delete rooms older than the configured room lifetime.'

    def handle(self, *args, **options):
        deleted_count, _ = purge_expired_rooms()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} expired room(s).'))