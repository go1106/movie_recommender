from rest_framework import serializers
from .models import Movie, Rating, Tag, Person, Cast, Genre

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['id', 'name', 'tmdb_id','imdb_id','profile_url']

class CastSerializer(serializers.ModelSerializer):
    person = PersonSerializer()
    class Meta:
        model = Cast
        fields = ("person", "character", "role_type", "job", "order")

class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    cast = CastSerializer(many=True, read_only=True)
    class Meta:
        model = Movie
        fields = (
            "id","slug","title","original_title","release_year","overview","poster_url",
            "runtime","popularity","vote_average","vote_count","avg_rating","rating_count",
            "tmdb_id","imdb_id","genres","tags","cast"
        )

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ("id","user","movie","rating","created_at","updated_at")






        

