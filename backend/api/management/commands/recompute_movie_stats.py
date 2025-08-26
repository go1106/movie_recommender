from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from api.models import Movie, Rating

class Command(BaseCommand):
    help = "Recompute Movie.avg_rating and rating_count in one pass."

    def handle(self, *args, **kwargs):
        # map movie_id -> (avg, cnt)
        agg = (Rating.objects
               .values("movie_id")
               .annotate(avg=Avg("rating"), cnt=Count("id")))
        updated = 0
        # build a dict for O(1) lookups
        agg_map = {row["movie_id"]: (row["avg"] or 0.0, row["cnt"] or 0) for row in agg}
        for m in Movie.objects.only("id").iterator():
            a, c = agg_map.get(m.id, (0.0, 0))
            Movie.objects.filter(pk=m.pk).update(avg_rating=a, rating_count=c)
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} movies."))
