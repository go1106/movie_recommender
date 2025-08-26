from django.shortcuts import render
from django.db.models import Avg, Value, F, Q
from django.db.models import Prefetch

from rest_framework import viewsets
from .models import Movie, Rating, Cast, Person, Genre
from .serializers import MovieSerializer, RatingSerializer
from django_filters.rest_framework import DjangoFilterBackend

from django_filters import rest_framework as filters
from django.db.models.functions import Coalesce

from .serializers import PersonSerializer, MovieSerializer, GenreSerializer
#from .utils import more_like_this, log_event
from .models import RecommendationCache 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet


from django.db.models import Count, Q, F, FloatField, Value
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Movie, Genre, Tag, Cast, Person, Rating
from .serializers import MovieSerializer, RatingSerializer

from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import RecommendationCache, Movie
from .serializers import MovieSerializer

User = get_user_model()

class RecCacheView(APIView):
    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail":"user not found"}, status=404)
        rc, _ = RecommendationCache.objects.get_or_create(user=user)
        movies = list(Movie.objects.filter(id__in=rc.items)
                      .prefetch_related("genres","tags","cast__person"))
        # keep original order of cached ids
        order = {mid:i for i, mid in enumerate(rc.items)}
        movies.sort(key=lambda m: order.get(m.id, 10**9))
        return Response(MovieSerializer(movies, many=True).data)
    
from rest_framework.decorators import api_view

@api_view(["GET"])
def trending(request):
    qs = (Movie.objects
          .order_by("-popularity","-vote_count","-avg_rating")[:40]
          .prefetch_related("genres","tags"))
    return Response(MovieSerializer(qs, many=True).data)

@api_view(["GET"])
def top_rated(request):
    qs = Movie.objects.order_by("-avg_rating","-rating_count","title")[:40]
    return Response(MovieSerializer(qs, many=True).data)



# ---- filters ----
class MovieFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    min_year = filters.NumberFilter(field_name="release_year", lookup_expr="gte")
    max_year = filters.NumberFilter(field_name="release_year", lookup_expr="lte")
    min_rating = filters.NumberFilter(field_name="avg_rating", lookup_expr="gte")
    genre = filters.CharFilter(method="filter_genre")
    tag = filters.CharFilter(method="filter_tag")

    def filter_genre(self, qs, name, value):
        return qs.filter(genres__name__iexact=value)

    def filter_tag(self, qs, name, value):
        return qs.filter(tags__name__iexact=value)

    class Meta:
        model = Movie
        fields = ["title","min_year","max_year","min_rating","genre","tag","release_year"]

# ---- viewset ----
class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (Movie.objects
                .all()
                .prefetch_related("genres","tags","cast__person")
                .order_by("-avg_rating","-rating_count","-popularity","title"))
    serializer_class = MovieSerializer
    filterset_class = MovieFilter
    filter_backends = (filters.DjangoFilterBackend,)
    permission_classes = [AllowAny]
    lookup_field = "slug"  # allows /api/movies/the-matrix-1999/

    @action(detail=True, methods=["get"])
    def more_like_this(self, request, slug=None):
        """Simple content-based: overlap on genres + tags + top cast."""
        base = self.get_object()

        # candidate pool: share any genre OR tag OR cast person
        genre_ids = list(base.genres.values_list("id", flat=True))
        tag_ids   = list(base.tags.values_list("id", flat=True))
        people_ids = list(Person.objects.filter(credits__movie=base, credits__role_type="cast")
                          .values_list("id", flat=True)[:12])

        candidates = (Movie.objects.exclude(pk=base.pk)
                      .filter(Q(genres__in=genre_ids) | Q(tags__in=tag_ids) | Q(cast__person__in=people_ids))
                      .distinct()
                      .prefetch_related("genres","tags","cast__person"))

        # quick scores (in python for clarity)
        def jaccard(a, b):
            if not a or not b: return 0.0
            A, B = set(a), set(b)
            return len(A & B) / float(len(A | B))

        base_genres = set(genre_ids)
        base_tags = set(tag_ids)
        base_people = set(people_ids)

        scored = []
        for m in candidates[:1000]:  # cap for safety
            g = set(m.genres.values_list("id", flat=True))
            t = set(m.tags.values_list("id", flat=True))
            p = set(Person.objects.filter(credits__movie=m, credits__role_type="cast")
                    .values_list("id", flat=True)[:12])

            s = 0.50 * jaccard(base_genres, g) + 0.30 * jaccard(base_people, p) + 0.20 * jaccard(base_tags, t)
            # small boost for high avg rating
            s += 0.05 * (m.avg_rating or 0)
            scored.append((s, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [m for _, m in scored[:20]]
        return Response(self.get_serializer(top, many=True).data)
    
class MovieFilter(filters.FilterSet):
    title     = filters.CharFilter(field_name="title", lookup_expr="icontains")
    min_year  = filters.NumberFilter(field_name="release_year", lookup_expr="gte")
    max_year  = filters.NumberFilter(field_name="release_year", lookup_expr="lte")
    min_rating= filters.NumberFilter(field_name="avg_rating", lookup_expr="gte")
    genre     = filters.CharFilter(field_name="genres__name", lookup_expr="iexact")
    tag       = filters.CharFilter(field_name="tags__name",   lookup_expr="iexact")

    class Meta:
        model = Movie
        fields = []   # <-- IMPORTANT: do not include custom names here

class RatingViewSet(mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]


from rest_framework.views import APIView

class RecommendView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username=None):
        """Recommend unseen movies for a username like 'u123' (MovieLens)."""
        if not username:
            return Response({"detail":"username required, e.g. /api/recommend/u123"}, status=400)

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail":"user not found"}, status=404)

        # user's liked movies and top genres/tags
        liked_qs = Rating.objects.filter(user=user, rating__gte=4.0).values_list("movie_id", flat=True)
        top_genres = (Genre.objects
                      .filter(movies__ratings__user=user, movies__ratings__rating__gte=4.0)
                      .annotate(cnt=Count("id"))
                      .order_by("-cnt")
                      .values_list("id", flat=True)[:5])
        top_tags = (Tag.objects
                    .filter(movies__ratings__user=user, movies__ratings__rating__gte=4.0)
                    .annotate(cnt=Count("id"))
                    .order_by("-cnt")
                    .values_list("id", flat=True)[:10])

        # candidates = unseen
        qs = (Movie.objects.exclude(id__in=liked_qs)
              .prefetch_related("genres","tags")
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
        )

        return Response(MovieSerializer(qs[:40], many=True).data)





"""
class MovieViewSet(viewsets.ModelViewSet):

    serializer_class = MovieSerializer

    # Enable filtering, searching, and ordering

    filter_backends = [DjangoFilterBackend,filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MoviFilter
    
    #filterset_fields = ['genres','average_rating']  # Allow filtering by year and genres
    search_fields = ['title']  # Assuming Movie model has 'title' and 'description' fields
    
    ordering_fields = ['title', 'average_rating', 'year']  # Allow ordering by these fields
    ordering = ['-average_rating']  # Default ordering by title   
    #pagination_class = None  # Disable pagination for simplicity, can be customized as needed

    def get_queryset(self):
        return(
            Movie.objects
                .annotate(average_rating=Coalesce(Avg('rating__rating'), Value(0.0)))
                .prefetch_related(
                    Prefetch(
                        'castings', 
                        queryset=MovieCast.objects
                            .select_related('person')
                            .order_by("order", 'id')
                    )
                )
        )

  
       
"""
