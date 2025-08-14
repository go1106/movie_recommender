# api/migrations/00xx_backfill_overview_not_null.py
from django.db import migrations

def backfill_overview(apps, schema_editor):
    Movie = apps.get_model("api", "Movie")
    Movie.objects.filter(overview__isnull=True).update(overview="")

class Migration(migrations.Migration):
    dependencies = [("api", "0013_alter_movie_slug")]
    operations = [migrations.RunPython(backfill_overview, migrations.RunPython.noop)]
