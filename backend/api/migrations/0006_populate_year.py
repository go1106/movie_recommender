from django.db import migrations
import re

def populate_year(apps, schema_editor):
    Movie = apps.get_model('api', 'Movie')
    for movie in Movie.objects.all():
        # Extract year from title using regex
        match = re.search(r'\((\d{4})\)', movie.title)
        if match:
            year = int(match.group(1))
            movie.year = year
            movie.save()

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_movie_average_rating_movie_year'),  # Adjust this to your last migration file
    ]

    operations = [
        migrations.RunPython(populate_year),
    ]