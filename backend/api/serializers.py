from rest_framework import serializers
from .models import Movie, Rating, Tag, Person, Cast, Genre, Tagging, Review
from django.contrib.auth import get_user_model

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

#class RatingSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Rating
#        fields = ("id","user","movie","rating","created_at","updated_at")

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
    def create(self, validated):
        user = User(username=validated["username"], email=validated.get("email",""))
        user.set_password(validated["password"])
        user.save()
        return user

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["id", "movie", "rating"]  # user is implied
    def create(self, data):
        data["user"] = self.context["request"].user
        return super().create(data)

class TaggingSerializer(serializers.ModelSerializer):
    # accept either tag id or a tag name
    tag_name = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = Tagging
        fields = ["id", "movie", "tag", "tag_name"]
    def validate(self, attrs):
        if not attrs.get("tag") and not attrs.get("tag_name"):
            raise serializers.ValidationError("Provide tag or tag_name.")
        return attrs
    def create(self, data):
        req = self.context["request"]
        data["user"] = req.user
        tag = data.get("tag")
        tag_name = data.pop("tag_name", None)
        if not tag and tag_name:
            t, _ = Tag.objects.get_or_create(name=tag_name.strip())
            data["tag"] = t
        return super().create(data)

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "movie", "title", "body"]
        #read_only_fields = ["created_at"]
    def create(self, data):
        data["user"] = self.context["request"].user
        return super().create(data)






        

