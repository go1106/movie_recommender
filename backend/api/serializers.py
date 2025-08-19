from rest_framework import serializers
from .models import Movie, Rating, MovieTag, Tag, Person, MovieCast, Genre

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['id', 'name','profile_url']

class MovieCastSerializer(serializers.ModelSerializer):
    person = PersonSerializer(read_only=True)

    class Meta:
        model = MovieCast
        fields = ['movie', 'person','character']

#class MovieSerializer(serializers.ModelSerializer):
    #average_rating = serializers.SerializerMethodField()
    #class Meta:
    #    model = Movie
    #    fields = ['movieId', 'title', 'genres', 'year', 'average_rating']
    #def get_average_rating(self, obj):
    #    ratings = Rating.objects.filter(movie=obj)

    #    if ratings.exists():
    #        return round(sum(rating.rating for rating in ratings) / len(ratings),2)
        
       
    #    return None
    
    




class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    castings = MovieCastSerializer(many=True, read_only=True)
    class Meta:
        model = Movie
        fields = [
            'movieId', 'title', 'overview', 'poster_url', 
            'slug', 'rating_count', 'avg_rating', 'year', 'genres', 'castings'
        ]
        read_only_fields = ['slug', 'rating_count', 'avg_rating']  # Make these fields read-only

class RatingSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Rating
        fields = ['userId', 'movie', 'rating']
        read_only_fields = ['movie']  # Make movie read-only to prevent direct assignment
