from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, F, FloatField, Value
from django.db.models.functions import Coalesce
from api.models import Movie, Genre, Tag, Rating, RecommendationCache

User = get_user_model()

class Command(BaseCommand):
    help = "Build RecommendationCache.items for all users (top 50)."

    def add_arguments(self, parser):
        parser.add_argument("--limit-users", type=int, default=None)
        parser.add_argument("--top-k", type=int, default=50)

    def handle(self, *args, **opts):
        k = opts["top_k"]
        users = User.objects.all().order_by("id")
        if opts["limit_users"]:
            users = users[:opts["limit_users"]]
        built = 0

        for u in users.iterator():
            liked = Rating.objects.filter(user=u, rating__gte=4.0).values_list("movie_id", flat=True)
            top_genres = (Genre.objects
                          .filter(movies__ratings__user=u, movies__ratings__rating__gte=4.0)
                          .annotate(c=Count("id")).order_by("-c").values_list("id", flat=True)[:5])
            top_tags = (Tag.objects
                        .filter(movies__ratings__user=u, movies__ratings__rating__gte=4.0)
                        .annotate(c=Count("id")).order_by("-c").values_list("id", flat=True)[:10])

            qs = (Movie.objects.exclude(id__in=liked)
                  .annotate(
                      shared_genres=Count("genres", filter=Q(genres__in=top_genres), distinct=True),
                      shared_tags=Count("tags", filter=Q(tags__in=top_tags), distinct=True),
                      score=(
                          Coalesce(F("avg_rating"), Value(0.0, output_field=FloatField())) * 0.25 +
                          Coalesce(F("popularity"), Value(0.0, output_field=FloatField())) * 0.05 +
                          Coalesce(F("vote_average"), Value(0.0, output_field=FloatField())) * 0.05 +
                          Coalesce(F("rating_count"), Value(0.0, output_field=FloatField())) * 0.02 +
                          F("shared_genres") * 0.40 +
                          F("shared_tags") * 0.23
                      )
                  )
                  .order_by("-score","-avg_rating","-rating_count","title")
                  .values_list("id", flat=True)[:k])

            rc, _ = RecommendationCache.objects.get_or_create(user=u)
            rc.items = list(qs)
            rc.save(update_fields=["items"])
            built += 1

        self.stdout.write(self.style.SUCCESS(f"Built rec cache for {built} users."))
