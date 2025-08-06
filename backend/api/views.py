from django.shortcuts import render
from django.db.models import Avg

from rest_framework import viewsets, filters
from .models import Movie, Rating
from .serializers import MovieSerializer, RatingSerializer

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.annotate(
        average_rating=Avg('rating__rating'))
        
    serializer_class = MovieSerializer 
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']  # Assuming Movie model has 'title' and 'description' fields
    ordering_fields = ['title', 'average_rating', 'year']  # Allow ordering by these fields
    ordering = ['-average_rating']  # Default ordering by title   
    #pagination_class = None  # Disable pagination for simplicity, can be customized as needed

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer


