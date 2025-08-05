from rest_framework import serializers
from .models import Movie, Rating   

class MovieSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    class Meta:
        model = Movie
        fields = ['movieId', 'title', 'genres', 'average_rating']
    def get_average_rating(self, obj):
        ratings = Rating.objects.filter(movie=obj)

        if ratings.exists():
            return round(sum(rating.rating for rating in ratings) / len(ratings),2)
        return None

class RatingSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Rating
        fields = ['userId', 'movie', 'rating']
        read_only_fields = ['movie']  # Make movie read-only to prevent direct assignment