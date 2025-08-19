from django.db import models
from django.conf import settings
from django.utils.text import slugify

#----lookups-----

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)  # Optional field for TMDb ID

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

#----core models-----

class Movie(models.Model):
    #id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    movieId = models.IntegerField(primary_key=True)  # Unique identifier for the movie
    title = models.CharField(max_length=255, db_index=True)  # Title of the movie
    #genres_text = models.CharField(max_length=255) # remove later, use Genre model
    #average_rating = models.FloatField(null=True, blank=True)

    year = models.IntegerField(null=True, blank=True)  # Optional field for year of release 

    overview = models.TextField(blank=True)  # Optional field for movie overview
    poster_url = models.URLField( null=True, blank=True) 
    imdb_id = models.CharField(max_length=20, null=True, blank=True)  # Optional field for IMDb ID
    tmdb_id = models.CharField(max_length=20, null=True, blank=True, db_index=True)  # Optional field for TMDb ID
    #new denormalized fields
    slug = models.SlugField(max_length=255, unique=True, blank=True)  # Slug field for URL-friendly names
    rating_count = models.IntegerField(default=0)  # Count of ratings received
    average_rating = models.FloatField(default=0.0,db_index=True)  # Average rating of the movie

    # new normalized genres+tags
    tags = models.ManyToManyField(Tag, through='MovieTag', related_name='movies', blank=True)  # Many-to-many relationship with Tag model
    genres = models.ManyToManyField(Genre, related_name='movies', blank=True)  # Many-to-many relationship with

    class Meta:
        indexes = [
            
            models.Index(fields=['year']),
            models.Index(fields=['average_rating','rating_count']),
        ]

    
    

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.title}-{self.year or ''}") or "movie"
            self.slug = f"{base}-{self.movieId}"
        super().save(*args, **kwargs)
                
        
    def __str__(self):
        return self.title

class Rating(models.Model):
    userId = models.IntegerField(db_index=True)  # Assuming userId is an integer, adjust as needed
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    rating = models.FloatField()

    #timestamp = models.DateTimeField(auto_now_add=True) 
    class Meta:
        unique_together = ('userId', 'movie')
        indexes = [
            models.Index(fields=['movie', 'rating'])
        ]

    def __str__(self):
        return f'User {self.userId} rated {self.movie.title} with {self.rating}'



class MovieTag(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    userId = models.IntegerField(null=True, blank=True)  # Assuming you want to track which user added the tag

     # Ensure a user can only tag a movie once with a specific tag
    class Meta:
        unique_together = (('movie', 'tag', 'userId'),)

    def __str__(self):
        return f'{self.movie.title} - {self.tag.name}'

class Person(models.Model):
    name = models.CharField(max_length=255,db_index=True)  # Name of the person (actor, director, etc.)
    tmdb_id = models.CharField(max_length=20, unique=True, null=True,blank=True)  # Unique identifier for TMDb
    imdb_id = models.CharField(max_length=20, unique=True, null =True,blank=True)  # Unique identifier for IMDb
    profile_url = models.URLField(null=True, blank=True)  # Optional field for profile URL

    def __str__(self):
        return self.name
class MovieCast(models.Model):
    ROLE_TYPES = (
        ('cast', 'Cast'),
        ('crew', 'Crew'),
        
        # Add more roles as needed
    )
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='castings')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='credits')

    character = models.CharField(max_length=255)  # e.g., 'actor', 'director', etc.
    order = models.IntegerField(default=999)  # Optional field to specify order of appearance


    role_type = models.CharField(max_length=16, choices=ROLE_TYPES, default='cast')  # Type of role (cast, crew, etc.)
    job = models.CharField(max_length=64, blank=True, default="")  # Optional field for job title (e.g., director, writer)
    
    class Meta:
        unique_together = ('movie', 'person','role_type',"job")  # Ensure a person can only have one role per movie
        ordering = ['order', 'id']  # Order by appearance and character

    def __str__(self):
        label = self.character or self.job or 'Unknown Role'
        return f'{self.person.name} as {label} in {self.movie.title}'
    
class Review(models.Model):
    userId = models.IntegerField(db_index=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    title = models.CharField(max_length=120, blank=True, default='')
    body = models.TextField()
    spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class List(models.Model):
    LIST_TYPES = (('watch','Watchlist'), ('seen','Seen'), ('custom','Custom'))
    userId = models.IntegerField(db_index=True)
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=16, choices=LIST_TYPES, default='custom')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('userId','name'),)

class ListItem(models.Model):
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='items')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('list','movie'),)
        ordering = ['position','-created_at']



# --- Analytics & Recommender ---

class Event(models.Model):
    """
    Lightweight event log for feed/recs UX:
    - impression: item shown
    - click: item opened
    - like/dismiss/rate: feedback actions
    """
    ACTIONS = (
        ('impression','impression'),
        ('click','click'),
        ('like','like'),
        ('dismiss','dismiss'),
        ('rate','rate'),
    )
    userId = models.IntegerField(null=True, blank=True, db_index=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True, related_name='events')
    action = models.CharField(max_length=12, choices=ACTIONS)
    context = models.JSONField(default=dict, blank=True)  # e.g. {"algo":"hybrid","slot":3}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['userId','action','created_at']),
            models.Index(fields=['action','created_at']),
        ]

class RecommendationCache(models.Model):
    """
    Snapshot of top-K for a user (store movieId ints).
    Keep TTL app-side or refresh on demand.
    """
    userId = models.IntegerField(unique=True, db_index=True)
    items = models.JSONField(default=list, blank=True)   # e.g., [123, 456, 789]
    model_version = models.CharField(max_length=32, default='v1')
    updated_at = models.DateTimeField(auto_now=True)

class Embedding(models.Model):
    """
    Generic vector store. Start with BinaryField (packed float32).
    Later you can migrate to pgvector.
    """
    OBJECT_TYPES = (('movie','movie'), ('user','user'), ('tag','tag'))
    object_type = models.CharField(max_length=8, choices=OBJECT_TYPES)
    object_id = models.IntegerField(db_index=True)  # movieId, userId, or Tag.pk
    dim = models.IntegerField()
    vector = models.BinaryField()                   # pack with numpy.tobytes()
    model_version = models.CharField(max_length=32, default='v1')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('object_type','object_id','model_version'),)
        indexes = [
            models.Index(fields=['object_type','model_version']),
            models.Index(fields=['object_id']),
        ]


