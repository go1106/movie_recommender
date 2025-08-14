import os, time, requests
from typing import List, Dict, Any, Optional
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Movie, Person, MovieCast
# FETCH USING TMDB API, IMPORT DATA INTO MOVIE(OVERVIEW, POSTER_URL), MOVIECAST(PERSON, CHARACTER),PERSON(NAME, TMDB_ID, IMDB_ID, PROFILE_URL)

TMDB_API_URL = "https://api.themoviedb.org/3"
API_KEY = os.environ.get('TMDB_API_KEY')
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"


class Command(BaseCommand):
    help = 'fetch poster_url, overview, cast/person images from TMDB and update the database'

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Maximum number of movies to process")
        parser.add_argument("--sleep", type=float, default=0.25, help="Sleep time between API calls to avoid rate limiting")
        parser.add_argument("--top_cost", type=int, default=12, help="Top cost for TMDB API calls")
        parser.add_argument("--movieId", type=int, help="Fetch data for a specific movie by movieId")
        parser.add_argument("--tmdb_id", type=int, help="Fetch data for a specific movie by TMDB ID")
        parser.add_argument("--only_missing", action='store_true', help="Only fetch movies that are missing poster_url or overview")
        parser.add_argument("--force_overwrite", action='store_true', help="Force overwrite existing poster_url or overview")

    def handle(self, *args, **opts):
        if not API_KEY:
            self.stdout.write(self.style.ERROR("API_KEY is not set. Please set it in your environment variables."))
            return

        qs = Movie.objects.exclude(tmdb_id__isnull=True).order_by('movieId')
        if opts.get("movieId"):
            qs = qs.filter(movieId=opts['movieId'])
        if opts.get('tmdb_id'):
            qs = qs.filter(tmdb_id=opts['tmdb_id'])
        if opts.get('limit'):
            qs = qs[:opts['limit']]
        
        only_missing = opts.get('only_missing', False)
        force_overwrite = opts.get('force_overwrite', False)
        sleep = opts.get('sleep')
        top_cost = opts.get('top_cost')

        person_imdb_cache: Dict[int, Optional[str]] = {}
        processed = 0
        updated_movies =0
        created_casts = 0
        updated_casts =0
        
        for movie in qs:
            processed += 1
            try:
                movie_data = self._fetch_movie_with_credits(movie.tmdb_id)
                changed_fields:List[str] = {}

                poster_url = movie_data.get('poster_path')
                overview = (movie_data.get('overview') or"").strip()
                if poster_url:
                    poster_url = IMG_BASE_URL + poster_url
                    if not movie.poster_url or force_overwrite:
                        movie.poster_url = poster_url
                        changed_fields.append('poster_url')
                if overview and (not movie.overview or force_overwrite):
                    if movie.overview != overview:
                        movie.overview = overview
                        changed_fields.append('overview')   
                if changed_fields:
                    movie.save(update_fields=changed_fields)
                    updated_movies += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated movie {movie.movieId} - {movie.title} with fields: {', '.join(changed_fields)}"))
                
                # Process cast
                castings = movie_data.get('credits', {}).get('cast', [])
                for cast in castings:
                    person_tmdb_id = cast.get('id')
                    person_name = cast.get('name')
                    character = cast.get('character', '').strip()
                    if not person_tmdb_id or not person_name or not character:
                        continue
                    
                    # Check if person already exists
                    person, created = Person.objects.get_or_create(
                        tmdb_id=person_tmdb_id,
                        defaults={'name': person_name}
                    )
                    
                    # Fetch IMDb ID if not already cached
                    if person.tmdb_id not in person_imdb_cache:
                        imdb_id = self._fetch_person_imdb_id(person.tmdb_id, sleep)
                        person_imdb_cache[person.tmdb_id] = imdb_id
                        if imdb_id:
                            person.imdb_id = imdb_id
                            person.save(update_fields=['imdb_id'])
                    
                    # Create or update MovieCast
                    movie_cast, created_cast = MovieCast.objects.update_or_create(
                        movie=movie,
                        person=person,
                        defaults={'character': character}
                    )
                    
                    if created_cast:
                        created_casts += 1
                        self.stdout.write(self.style.SUCCESS(f"Created MovieCast for {movie.title} - {person.name} as {character}"))
                    else:
                        updated_casts += 1
                        self.stdout.write(self.style.SUCCESS(f"Updated MovieCast for {movie.title} - {person.name} as {character}"))    
                
                    #get or create person
                    person, created = Person.objects.get_or_create(
                        tmdb_id=person_tmdb_id,
                        defaults={'name': person_name, 'profile_url': cast.get('profile_path', None)}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created Person {person.name} with TMDB ID {person.tmdb_id}"))
                    else:
                        self.stdout.write(self.style.SUCCESS(f"Person {person.name} already exists with TMDB ID {person.tmdb_id}"))
                    
                    # Update or create MovieCast
                    #fetch imdb_id for person
                    if person.tmdb_id not in person_imdb_cache:
                        imdb_id = self._fetch_person_imdb_id(person.tmdb_id, sleep)
                        person_imdb_cache[person.tmdb_id] = imdb_id
                        if imdb_id:
                            person.imdb_id = imdb_id
                            person.save(update_fields=['imdb_id'])      



                
                time.sleep(sleep)  # Respect TMDB's rate limits
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Error fetching movie with TMDB ID {movie.tmdb_id}: {e}"))
                continue    
            
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} movies."))
        self.stdout.write(self.style.SUCCESS(f"Updated {updated_movies} movies with poster_url or overview."))
        self.stdout.write(self.style.SUCCESS(f"Created {created_casts} new MovieCast entries."))
        self.stdout.write(self.style.SUCCESS(f"Updated {updated_casts} existing MovieCast entries."))
        self.stdout.write(self.style.SUCCESS(f"Cached IMDb IDs for {len(person_imdb_cache)} persons.")) 
                

            
       
        
        
    def _fetch_movie_with_credits(self, tmdb_id: int) -> dict:
        """Fetch movie details and credits from TMDB."""
        url = f"{TMDB_API_URL}/movie/{tmdb_id}"
        params = {
            "api_key": API_KEY,
            "language": "en-US",
            "append_to_response": "credits"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    def _fetch_person_imdb_id(self, tmdb_id: int, sleep:float) -> Optional[str]:

        """Fetch IMDb ID for a person from TMDB."""
        try:
            url = f"{TMDB_API_URL}/person/{tmdb_id}"
            params = {
                "api_key": API_KEY,
                "language": "en-US",
                "timeout": 10  # Set a timeout to avoid hanging requests
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            imdb_id = data.get('external_ids', {}).get('imdb_id') or data.get('imdb_id') or None

            
            time.sleep(sleep)  # Respect TMDB's rate limits
            return data.get('imdb_id')
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error fetching person with TMDB ID {tmdb_id}: {e}"))
            return None
    