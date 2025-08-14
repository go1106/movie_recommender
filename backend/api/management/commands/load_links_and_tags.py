from django.core.management.base import BaseCommand
from api.models import Movie, Tag, MovieTag
import pandas as pd
from django.db import transaction
import csv  
import pandas as pandas

class Command(BaseCommand):
    help = 'Load movies and ratings from CSV files'

    

    def handle(self, *args, **kwargs):

        tags_df = pandas.read_csv('api/data/tags.csv')
        links_df = pandas.read_csv('api/data/links.csv')
       
        for index, row in links_df.iterrows():
            try:
                movie = Movie.objects.get(movieId=row['movieId'])
                movie.imdb_id = row['imdbId']
                movie.tmdb_id = row['tmdbId']
                movie.save()
            except Movie.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Movie with ID {row["movieId"]} does not exist. Skipping link update.'))
                continue    

        for index, row in tags_df.iterrows():
            Tag.objects.get_or_create(
                name=row['tag']
            )
        for index, row in tags_df.iterrows():
            try:
                movie = Movie.objects.get(movieId=row['movieId'])
                tag = Tag.objects.get(name=row['tag'])
                MovieTag.objects.get_or_create(
                    movie=movie,
                    tag=tag,
                    userId=row['userId']
                )
            except Movie.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Movie with ID {row["movieId"]} does not exist. Skipping tag assignment.'))
                continue    
            except Tag.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Tag {row["tag"]} does not exist. Skipping tag assignment.'))
                continue
      
            
        self.stdout.write(self.style.SUCCESS('Successfully loaded...'))