from django.core.management.base import BaseCommand
from api.models import Movie, Rating
import csv  
import pandas as pandas

class Command(BaseCommand):
    help = 'Load movies and ratings from CSV files'

    

    def handle(self, *args, **kwargs):

        movies_df = pandas.read_csv('api/data/movies.csv')
        ratings_df = pandas.read_csv('api/data/ratings.csv')
       
        for index, row in movies_df.iterrows():
            Movie.objects.get_or_create(
                movieId=row['movieId'],
                defaults={
                    'title': row['title'],  
                    'genres': row['genres']
                }
            
            )
        for index, row in ratings_df.iterrows():
            try:
                movie = Movie.objects.get(movieId=row['movieId'])
                Rating.objects.get_or_create(
                userId=row['userId'],
                movie=movie,
                rating=row['rating']
                )
            except Movie.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Movie with ID {row["movieId"]} does not exist. Skipping rating.'))
                continue
            
            
        self.stdout.write(self.style.SUCCESS('Successfully loaded movies and ratings'))
        