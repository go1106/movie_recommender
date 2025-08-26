# app/models.py
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.db.models.functions import Lower

User = settings.AUTH_USER_MODEL

class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
        

class Genre(TimeStamped):
    name = models.CharField(max_length=64, unique=True)
    tmdb_id = models.IntegerField(null=True, blank=True, unique=True)
    def __str__(self): return self.name
    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("name"), name="uniq_genre_lower_name_ci_v1"),
        ]

class Tag(TimeStamped):
    name = models.CharField(max_length=64, unique=True)
    def __str__(self): return self.name
    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("name"), name="uniq_tag_lower_name_ci_v1"),
        ]

class Person(TimeStamped):
    tmdb_id = models.IntegerField(null=True, blank=True, unique=True)
    name = models.CharField(max_length=128, db_index=True)
    imdb_id = models.CharField(max_length=16, null=True, blank=True, unique=True)
    profile_url = models.URLField(null=True, blank=True)
    def __str__(self): return self.name
    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("name"), name="uniq_person_lower_name_ci_v1"),
        ]

class Provider(TimeStamped):
    """Streaming/provider info (optional)"""
    name = models.CharField(max_length=64, unique=True)
    def __str__(self): return self.name
    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("name"), name="uniq_provider_lower_name_ci_v1"),
        ]

class Movie(TimeStamped):
    tmdb_id = models.IntegerField(null=True, blank=True, unique=True)
    imdb_id = models.CharField(max_length=16, null=True, blank=True, unique=True)
    title = models.CharField(max_length=256, db_index=True)
    original_title = models.CharField(max_length=256, null=True, blank=True)
    release_year = models.IntegerField(null=True, blank=True, db_index=True)
    overview = models.TextField(blank=True, default="")
    poster_url = models.URLField(null=True, blank=True)
    runtime = models.IntegerField(null=True, blank=True)  # minutes
    popularity = models.FloatField(default=0.0)           # TMDB pop or your own
    vote_average = models.FloatField(default=0.0)         # external avg (tmdb/imdb)
    vote_count = models.IntegerField(default=0)

    # denormalized for speed (updated by signals or cron)
    avg_rating = models.FloatField(default=0.0, db_index=True)
    rating_count = models.IntegerField(default=0)

    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    tags = models.ManyToManyField(Tag, related_name="movies", blank=True)
    providers = models.ManyToManyField(Provider, related_name="movies", blank=True)

    slug = models.SlugField(max_length=300, unique=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["release_year"]),
            models.Index(fields=["-avg_rating", "-rating_count"]),
            models.Index(fields=["-popularity"]),
            models.Index(fields=["title"]),  # for LIKE/startswith queries
        ]
        
        constraints = [
            models.UniqueConstraint(fields=["title", "release_year"], name="uniq_title_year", condition=models.Q(tmdb_id__isnull=True)),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.title}-{self.release_year or ''}"
            slug = slugify(base)[:300]
            n = 1
            while Movie.objects.filter(slug=slug).exists():
                slug = f"{slugify(base)}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.title} ({self.release_year or '—'})"

class Cast(TimeStamped):
    """Through table for credits"""
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="cast")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="credits")
    character = models.CharField(max_length=128, blank=True, default="")
    order = models.IntegerField(default=999)
    role_type = models.CharField(max_length=16, choices=[("cast","Cast"),("crew","Crew")], default="cast")
    job = models.CharField(max_length=64, blank=True, default="")  # e.g., Director
    class Meta:
        unique_together = [("movie","person","role_type","job")]
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["movie", "person", "role_type", "job", "character"],
                                    name="uniq_credit_per_character")
            ]

# Engagement & social
from django.core.validators import MinValueValidator, MaxValueValidator

class Rating(TimeStamped):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="ratings")
    rating = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])  # 0.5–5.0
    class Meta:
        unique_together = [("user","movie")]
        indexes = [models.Index(fields=["movie","rating"]), models.Index(fields=["user"])]
        constraints = [models.CheckConstraint(check=models.Q(rating__gte=0.0) & models.Q(rating__lte=5.0), name="rating_range")]

class Review(TimeStamped):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
    title = models.CharField(max_length=120, blank=True, default="")
    body = models.TextField()
    spoiler = models.BooleanField(default=False)


class List(TimeStamped):
    """Watchlist/Seen/Custom lists"""
    LIST_TYPES = [("watch","Watchlist"), ("seen","Seen"), ("custom","Custom")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lists")
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=16, choices=LIST_TYPES, default="custom")
    class Meta:
        unique_together = [("user","name")]

class ListItem(TimeStamped):
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name="items")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="+")
    position = models.IntegerField(default=0)
    class Meta:
        unique_together = [("list","movie")]
        ordering = ["position","-created_at"]

class Follow(TimeStamped):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    followee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    class Meta:
        unique_together = [("follower","followee")]

# Telemetry for analytics & online learning

class Event(TimeStamped):
    """Track actions for analytics and CTR (view, click, like, dismiss)"""
    ACTIONS = [("impression","impression"),("click","click"),("like","like"),("dismiss","dismiss"),("rate","rate")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events", null=True, blank=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="events", null=True, blank=True)
    action = models.CharField(max_length=12, choices=ACTIONS)
    context = models.JSONField(default=dict, blank=True)  # e.g., {"slot":3,"algo":"hybrid"}

# Recommender artifacts (cache + embeddings)

class RecommendationCache(TimeStamped):
    """Snapshot of top-K recommended IDs for a user (TTL enforced app-side/Redis preferred)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="rec_cache")
    items = models.JSONField(default=list, blank=True)  # [movie_id,...]
    model_version = models.CharField(max_length=32, default="v1")

class Embedding(TimeStamped):
    """Optional: store dense vectors for ANN search / hybrid scoring"""
    OBJECT_TYPES = [("movie","movie"), ("user","user"), ("tag","tag")]
    object_type = models.CharField(max_length=8, choices=OBJECT_TYPES)
    object_id = models.IntegerField(db_index=True)
    dim = models.IntegerField()
    vector = models.BinaryField()  # packed float32 (or use pgvector extension)
    model_version = models.CharField(max_length=32, default="v1")
    class Meta:
        unique_together = [("object_type","object_id","model_version")]
        indexes = [models.Index(fields=["object_type", "object_id", "model_version"])]



