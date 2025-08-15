from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from api.models import Event

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        since = timezone.now() - timedelta(days=7)
        top = (Event.objects.filter(action='click', created_at__gte=since, movie__isnull=False)
               .values('movie_id').annotate(c=Count('id')).order_by('-c')[:20])
        self.stdout.write(str(top))
