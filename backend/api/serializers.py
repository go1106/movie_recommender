from rest_framework import serializers
from .models import Movie, Rating   

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['movieId', 'title', 'genres']

class RatingSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Rating
        fields = ['userId', 'movie', 'rating']
        read_only_fields = ['movie']  # Make movie read-only to prevent direct assignment