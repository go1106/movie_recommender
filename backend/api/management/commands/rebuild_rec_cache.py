from django.core.management.base import BaseCommand
from api.models import RecommendationCache, Rating, Movie
from collections import defaultdict

class Command(BaseCommand):
    help = "Toy recs: top popular by average_rating (fallback). Replace with your hybrid model."

    def handle(self, *args, **kwargs):
        # naive popularity: avg_rating then rating_count
        popular_ids = list(
            Movie.objects.order_by('-average_rating','-rating_count')
            .values_list('movieId', flat=True)[:500]
        )
        # write a simple cache for all users seen in ratings
        user_ids = set(Rating.objects.values_list('userId', flat=True))
        for uid in user_ids:
            RecommendationCache.objects.update_or_create(
                userId=uid,
                defaults={"items": popular_ids[:50], "model_version":"v1"}
            )
        self.stdout.write(self.style.SUCCESS(f"Rebuilt cache for {len(user_ids)} users."))
