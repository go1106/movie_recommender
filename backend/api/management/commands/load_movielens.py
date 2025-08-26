import csv, os, re, time, math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import requests
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from api.models import (
    Movie, Genre, Tag, Provider, Person, Cast,  # or MovieCast alias if you kept it
    Rating, Event
)

User = get_user_model()

IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

def clean_int(x):
    if x in (None, "", "null"): return None
    if isinstance(x, float):
        return None if math.isnan(x) else int(x)
    try:
        return int(str(x).strip())
    except Exception:
        return None

def clean_str(x):
    if x is None: return ""
    return str(x).strip()

YEAR_RX = re.compile(r"\((\d{4})\)\s*$")

def split_genres(s):
    s = (s or "").strip()
    if not s or s == "(no genres listed)":
        return []
    return [g.strip() for g in s.split("|") if g.strip()]

def parse_title_year(raw_title):
    t = clean_str(raw_title)
    m = YEAR_RX.search(t)
    if m:
        year = int(m.group(1))
        title = t[:m.start()].strip()
        return title, year
    return t, None

def quantize_rating(x):
    # MovieLens ratings are floats like 3.5; store as Decimal(1 place)
    d = Decimal(str(x)).quantize(Decimal("0.0"), rounding=ROUND_HALF_UP)
    return d

def tmdb_get(api_key, path, params=None, sleep=0.25):
    url = f"https://api.themoviedb.org/3{path}"
    q = {"api_key": api_key, "language": "en-US"}
    if params:
        q.update(params)
    r = requests.get(url, params=q, timeout=20)
    # polite rate-limit
    time.sleep(sleep)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

class Command(BaseCommand):
    help = "Load MovieLens (movies, links, ratings, tags) and optionally enrich with TMDB."

    def add_arguments(self, parser):
        parser.add_argument("--dir", help="Directory containing movies.csv, ratings.csv, links.csv, tags.csv")
        parser.add_argument("--movies", help="Path to movies.csv")
        parser.add_argument("--links", help="Path to links.csv")
        parser.add_argument("--ratings", help="Path to ratings.csv")
        parser.add_argument("--tags", help="Path to tags.csv")
        parser.add_argument("--tmdb", action="store_true", help="Enrich movies from TMDB (overview/runtime/…)")
        parser.add_argument("--tmdb-credits", action="store_true", help="Also fetch credits and fill Cast/Person")
        parser.add_argument("--max", type=int, default=None, help="Limit number of movies to load (for testing)")
        parser.add_argument("--skip-ratings", action="store_true")
        parser.add_argument("--skip-tags", action="store_true")

    def handle(self, *args, **opts):
        base = Path(opts["dir"]).expanduser().resolve() if opts.get("dir") else None
        movies_csv  = Path(opts["movies"]).expanduser().resolve()  if opts.get("movies")  else (base / "movies.csv"  if base else None)
        links_csv   = Path(opts["links"]).expanduser().resolve()   if opts.get("links")   else (base / "links.csv"   if base else None)
        ratings_csv = Path(opts["ratings"]).expanduser().resolve() if opts.get("ratings") else (base / "ratings.csv" if base else None)
        tags_csv    = Path(opts["tags"]).expanduser().resolve()    if opts.get("tags")    else (base / "tags.csv"    if base else None)

        # sanity
        for pth, name in [(movies_csv, "movies.csv"), (links_csv, "links.csv")]:
            if not pth or not pth.exists():
                raise CommandError(f"Missing {name}: {pth}")

        tmdb_key = os.getenv("TMDB_API_KEY")
        if (opts["tmdb"] or opts["tmdb_credits"]) and not tmdb_key:
            self.stderr.write(self.style.WARNING("TMDB enrichment requested but TMDB_API_KEY not set. Skipping TMDB."))
            opts["tmdb"] = opts["tmdb_credits"] = False

        # 1) Load links into dict: movieId -> (imdb_id, tmdb_id)
        self.stdout.write("Loading links.csv …")
        id_map = {}  # movieId -> dict
        with links_csv.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                mid  = clean_int(row.get("movieId"))
                imdb = clean_str(row.get("imdbId"))
                tmdb = clean_int(row.get("tmdbId"))
                if mid is not None:
                    id_map[mid] = {"imdb": (f"tt{imdb}" if imdb and not imdb.startswith("tt") else imdb) or None,
                                   "tmdb": tmdb}

        # cache objects to cut queries
        genre_cache = {g.name: g.id for g in Genre.objects.all()}
        tag_cache   = {t.name: t.id for t in Tag.objects.all()}

        created_movies = updated_movies = 0

        # 2) Load movies + genres; optionally TMDB enrich
        self.stdout.write("Loading movies.csv …")
        with movies_csv.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                if opts["max"] and i > opts["max"]:
                    break

                movie_id = clean_int(row.get("movieId"))
                raw_title = row.get("title")
                title, year = parse_title_year(raw_title)
                genres = split_genres(row.get("genres"))

                link = id_map.get(movie_id, {})
                imdb_id = link.get("imdb")
                tmdb_id = link.get("tmdb")

                lookup = {}
                if tmdb_id: lookup["tmdb_id"] = tmdb_id
                elif imdb_id: lookup["imdb_id"] = imdb_id
                else: lookup = {"title": title, "release_year": year}

                defaults = {"title": title, "release_year": year}

                obj, is_created = Movie.objects.update_or_create(defaults=defaults, **lookup)
                created_movies += int(is_created)
                updated_movies += int(not is_created)

                # genres M2M
                if genres:
                    for gname in genres:
                        gid = genre_cache.get(gname)
                        if not gid:
                            gobj = Genre.objects.create(name=gname)
                            genre_cache[gname] = gobj.id
                            gid = gobj.id
                        obj.genres.add(gid)

                # IDs set if missing
                need_save = False
                if imdb_id and not obj.imdb_id:
                    obj.imdb_id = imdb_id; need_save = True
                if tmdb_id and not obj.tmdb_id:
                    obj.tmdb_id = tmdb_id; need_save = True

                # TMDB enrichment
                if tmdb_id and opts["tmdb"]:
                    try:
                        data = tmdb_get(tmdb_key, f"/movie/{tmdb_id}")
                        if data:
                            # set fields if available
                            obj.overview = data.get("overview") or obj.overview
                            obj.runtime = data.get("runtime") or obj.runtime
                            obj.popularity = data.get("popularity") or obj.popularity
                            obj.vote_average = data.get("vote_average") or obj.vote_average
                            obj.vote_count = data.get("vote_count") or obj.vote_count
                            poster_path = data.get("poster_path")
                            if poster_path:
                                obj.poster_url = f"{IMAGE_BASE}{poster_path}"
                            orig = data.get("original_title")
                            if orig and not obj.original_title:
                                obj.original_title = orig
                            need_save = True
                    except Exception as e:
                        self.stderr.write(self.style.WARNING(f"TMDB details failed for tmdb_id={tmdb_id}: {e}"))

                    if tmdb_id and opts["tmdb_credits"]:
                        try:
                            credits = tmdb_get(tmdb_key, f"/movie/{tmdb_id}/credits")
                            if credits and isinstance(credits, dict):
                                # up to top 15 cast
                                for c in (credits.get("cast") or [])[:15]:
                                    pid = clean_int(c.get("id"))
                                    name = clean_str(c.get("name"))
                                    order = clean_int(c.get("order")) or 999
                                    person, _ = Person.objects.get_or_create(tmdb_id=pid, defaults={"name": name or "Unknown"})
                                    if name and person.name != name and person.name == "Unknown":
                                        person.name = name; person.save(update_fields=["name"])
                                    Cast.objects.get_or_create(
                                        movie=obj, person=person, role_type="cast", job="", character=clean_str(c.get("character")),
                                        defaults={"order": order}
                                    )
                                # directors (crew)
                                for cr in (credits.get("crew") or []):
                                    if clean_str(cr.get("job")) == "Director":
                                        pid = clean_int(cr.get("id"))
                                        name = clean_str(cr.get("name"))
                                        person, _ = Person.objects.get_or_create(tmdb_id=pid, defaults={"name": name or "Unknown"})
                                        Cast.objects.get_or_create(
                                            movie=obj, person=person, role_type="crew", job="Director", character="",
                                            defaults={"order": 1}
                                        )
                        except Exception as e:
                            self.stderr.write(self.style.WARNING(f"TMDB credits failed for tmdb_id={tmdb_id}: {e}"))

                if need_save:
                    obj.save()

        self.stdout.write(self.style.SUCCESS(f"Movies upserted. created={created_movies}, updated={updated_movies}"))

        # 3) Ratings
        if not opts["skip_ratings"] and ratings_csv and ratings_csv.exists():
            self.stdout.write("Loading ratings.csv …")
            added = up = 0
            with ratings_csv.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    uid = clean_int(row.get("userId"))
                    mid = clean_int(row.get("movieId"))
                    rating = quantize_rating(row.get("rating"))
                    # user
                    user, _ = User.objects.get_or_create(username=f"u{uid}")
                    # movie (prefer tmdb mapping; else fallback by movieId we just imported)
                    link = id_map.get(mid, {})
                    movie = None
                    if link.get("tmdb"):
                        movie = Movie.objects.filter(tmdb_id=link["tmdb"]).first()
                    if not movie and link.get("imdb"):
                        movie = Movie.objects.filter(imdb_id=link["imdb"]).first()
                    if not movie:
                        # fallback: impossible if earlier step ran, but just in case
                        continue
                    obj, is_new = Rating.objects.update_or_create(user=user, movie=movie, defaults={"rating": rating})
                    added += int(is_new); up += int(not is_new)
            self.stdout.write(self.style.SUCCESS(f"Ratings upserted. created={added}, updated={up}"))

        # 4) Tags
        if not opts["skip_tags"] and tags_csv and tags_csv.exists():
            self.stdout.write("Loading tags.csv …")
            added = 0
            with tags_csv.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    uid = clean_int(row.get("userId"))
                    mid = clean_int(row.get("movieId"))
                    tag_name = clean_str(row.get("tag"))
                    if not tag_name:
                        continue
                    link = id_map.get(mid, {})
                    movie = None
                    if link.get("tmdb"):
                        movie = Movie.objects.filter(tmdb_id=link["tmdb"]).first()
                    if not movie and link.get("imdb"):
                        movie = Movie.objects.filter(imdb_id=link["imdb"]).first()
                    if not movie:
                        continue
                    # global tag attach
                    tid = tag_cache.get(tag_name)
                    if not tid:
                        tobj = Tag.objects.create(name=tag_name)
                        tag_cache[tag_name] = tobj.id
                        tid = tobj.id
                    movie.tags.add(tid)
                    # optional: log as Event for per-user history
                    user, _ = User.objects.get_or_create(username=f"u{uid}")
                    Event.objects.create(user=user, movie=movie, action="impression", context={"source":"movielens","tag":tag_name})
                    added += 1
            self.stdout.write(self.style.SUCCESS(f"Tags processed: {added}"))

        self.stdout.write(self.style.SUCCESS("Done."))
