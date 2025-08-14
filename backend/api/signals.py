# api/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Rating, Movie

def recompute(movie_id: int):
    agg = Rating.objects.filter(movie_id=movie_id).aggregate(
        avg=Avg('rating'), cnt=Count('id')
    )
    Movie.objects.filter(pk=movie_id).update(
        average_rating=round(agg['avg'] or 0.0, 2),
        rating_count=agg['cnt'] or 0
    )

@receiver(post_save, sender=Rating)
def rating_saved(sender, instance, **kwargs):
    recompute(instance.movie_id)

@receiver(post_delete, sender=Rating)
def rating_deleted(sender, instance, **kwargs):
    recompute(instance.movie_id)
