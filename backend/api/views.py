from django.shortcuts import render
from django.db.models import Avg, Value, F
from django.db.models import Prefetch

from rest_framework import viewsets, filters
from .models import Movie, Rating
from .serializers import MovieSerializer, RatingSerializer
from django_filters.rest_framework import DjangoFilterBackend

from django_filters import rest_framework as djfilters
from django.db.models.functions import Coalesce

class MoviFilter(djfilters.FilterSet):
    genres = djfilters.CharFilter(field_name='genres', lookup_expr='icontains')
    average_rating = djfilters.NumberFilter(field_name='average_rating', lookup_expr='gte')

    class Meta:
        model = Movie
        fields = ['genres', 'average_rating']   

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

  
       




class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer


