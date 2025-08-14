# api/migrations/00xx_recompute_all_ratings.py
from django.db import migrations
from django.db.models import Avg, Count

def recompute_all(apps, schema_editor):
    Movie = apps.get_model("api", "Movie")
    Rating = apps.get_model("api", "Rating")
    for row in (Rating.objects
                .values("movie_id")
                .annotate(avg=Avg("rating"), cnt=Count("id"))):
        Movie.objects.filter(pk=row["movie_id"]).update(
            average_rating=round(row["avg"] or 0.0, 2),
            rating_count=row["cnt"] or 0
        )

class Migration(migrations.Migration):
    dependencies = [("api", "0015_tighten_strings_and_ratings")]  # adjust if different
    operations = [migrations.RunPython(recompute_all, migrations.RunPython.noop)]
