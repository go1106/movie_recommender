from django.shortcuts import render

from rest_framework import viewsets, filters
from .models import Movie, Rating
from .serializers import MovieSerializer, RatingSerializer

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer 
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']  # Assuming Movie model has 'title' and 'description' fields
    

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer


