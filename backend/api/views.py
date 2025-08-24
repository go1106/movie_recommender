from django.shortcuts import render
from django.db.models import Avg, Value, F, Q
from django.db.models import Prefetch

from rest_framework import viewsets, filters
from .models import Movie, Rating, MovieCast, Person, Genre
from .serializers import MovieSerializer, RatingSerializer
from django_filters.rest_framework import DjangoFilterBackend

from django_filters import rest_framework as djfilters
from django.db.models.functions import Coalesce

from .serializers import PersonSerializer, MovieCastSerializer, MovieSerializer, GenreSerializer,MovieListSerializer
from .utils import more_like_this, log_event
from .models import RecommendationCache 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet


class MovieFilter(filters.FilterSet):
    q = filters.CharFilter(method="search")
    min_rating = filters.NumberFilter(method="filter_min_rating")
    max_rating = filters.NumberFilter(method="filter_max_rating")
    genre = filters.CharFilter(field_name="genres__name", lookup_expr="iexact")  # if you have a Genre model
    year = filters.NumberFilter(field_name="year")
    year_gte = filters.NumberFilter(field_name="year", lookup_expr="gte")
    year_lte = filters.NumberFilter(field_name="year", lookup_expr="lte")

    class Meta:
        model = Movie
        fields = ["genre", "year"]

    def search(self, qs, name, value):
        return qs.filter(
            Q(title__icontains=value) |
            Q(overview__icontains=value) |
            Q(cast__name__icontains=value)  # adjust to your relations
        ).distinct()

    def _with_avg(self, qs):
        return qs.annotate(avg_rating=Avg("ratings__rating"))

    def filter_min_rating(self, qs, name, value):
        return self._with_avg(qs).filter(avg_rating__gte=value)

    def filter_max_rating(self, qs, name, value):
        return self._with_avg(qs).filter(avg_rating__lte=value)

class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.all().prefetch_related("ratings")
    serializer_class = MovieSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = MovieFilter
    ordering_fields = ["title", "year", "avg_rating"]
    ordering = ["-id"]  # default

    def get_queryset(self):
        qs = super().get_queryset()
        # enable ordering by avg_rating safely
        if self.request.query_params.get("ordering") in ("avg_rating", "-avg_rating"):
            qs = qs.annotate(avg_rating=Avg("ratings__rating"))
        return qs

class MoviFilter(djfilters.FilterSet):
    genres = djfilters.CharFilter(field_name='genres', lookup_expr='icontains')
    average_rating = djfilters.NumberFilter(field_name='average_rating', lookup_expr='gte')

    class Meta:
        model = Movie
        fields = ['genres', 'average_rating']   
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
class MovieViewSet(ReadOnlyModelViewSet):
    serializer_class = MovieListSerializer
    filterset_fields = ["average_rating", "year", "genres__name"]
    search_fields = ["title", "overview"]
    ordering_fields = ["title", "year", "average_rating", "rating_count"]
    ordering = ["-average_rating", "-rating_count"]

    def get_queryset(self):
        return (
            Movie.objects.all()
            .prefetch_related("genres", Prefetch("castings", queryset=MovieCast.objects.select_related("person")))
        )



class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer


# views.py (pseudo)
class RecommendView(APIView):
    def get(self, req):
        uid = int(req.query_params.get("userId", 0)) or None
        items = []
        if uid:
            cache = RecommendationCache.objects.filter(userId=uid).first()
            if cache:
                items = cache.items
        if not items:
            items = list(Movie.objects.order_by('-average_rating','-rating_count')
                         .values_list('movieId', flat=True)[:20])
        # log impressions
        for i, mid in enumerate(items[:20]):
            log_event(uid, 'impression', mid, slot=i, algo='cache' if uid else 'popular')
        # return movie payloads
        qs = Movie.objects.filter(movieId__in=items)
        data = MovieSerializer(qs, many=True).data
        return Response(data)

class EventView(APIView):
    def post(self, req):
        uid = req.data.get("userId")
        action = req.data["action"]
        movie_id = req.data.get("movieId")
        ctx = req.data.get("context", {})
        log_event(uid, action, movie_id, **ctx)
        return Response({"ok": True})

class MoreLikeThisView(APIView):
    def get(self, req, movieId: int):
        ids = more_like_this(movieId, k=int(req.query_params.get("k",20)))
        qs = Movie.objects.filter(movieId__in=ids)
        return Response(MovieSerializer(qs, many=True).data)



