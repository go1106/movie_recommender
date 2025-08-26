# api/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Rating, Movie

@receiver([post_save, post_delete], sender=Rating)
def update_movie_rating(sender, instance, **kwargs):
    agg = Rating.objects.filter(movie=instance.movie).aggregate(
        avg=Avg('rating'), cnt=Count('id')
    )
    Movie.objects.filter(id=instance.movie_id).update(
        avg_rating=(agg['avg'] or 0.0),
        rating_count=agg['cnt'] or 0
    )

