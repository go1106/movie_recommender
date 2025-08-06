from django.db import models

# Create your models here.
class Movie(models.Model):
    movieId = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    genres = models.CharField(max_length=255) 
    #average_rating = models.FloatField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)  # Optional field for year of release  

    def __str__(self):
        return self.title

class Rating(models.Model):
    userId = models.IntegerField()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.FloatField()

    #timestamp = models.DateTimeField(auto_now_add=True) 
    class Meta:
        unique_together = ('userId', 'movie')
  


    def __str__(self):
        return f'User {self.userId} rated {self.movie.title} with {self.rating}'