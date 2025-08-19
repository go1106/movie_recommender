
# api/management/commands/tmdb_link_missing.py
import os, time, requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Movie

API_KEY = os.getenv("TMDB_API_KEY","feda2c7c12b2a9fbbea6a861c1367e30")
BASE = "https://api.themoviedb.org/3"

def _get(path, **params):
    if not API_KEY:
        raise CommandError("TMDB_API_KEY not set")
    params["api_key"] = API_KEY
    r = requests.get(f"{BASE}{path}", params=params, timeout=(5, 30))
    r.raise_for_status()
    return r.json()

def find_by_imdb(imdb_id):
    res = _get(f"/find/{imdb_id}", external_source="imdb_id")
    movies = res.get("movie_results") or []
    return str(movies[0]["id"]) if movies else None

class Command(BaseCommand):
    help = "Fill missing tmdb_id using imdb_id for movies that already failed tmdb import"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--sleep", type=float, default=0.2)

    @transaction.atomic
    def handle(self, *args, **opts):
        qs = Movie.objects.filter(poster_url__isnull=True).exclude(imdb_id__isnull=True)
        if opts["limit"]:
            qs = qs[:opts["limit"]]

        fixed = 0
        skipped = 0
        for m in qs.iterator(chunk_size=200):
            if not m.imdb_id:
                skipped += 1
                continue

            tmdb_id = None
            try:
                tmdb_id = find_by_imdb(m.imdb_id)
            except Exception as e:
                self.stderr.write(f"error imdb={m.imdb_id} ({e})")
                skipped += 1
                continue

            if tmdb_id:
                if opts["dry_run"]:
                    self.stdout.write(f"[DRY] movieId={m.movieId} imdb={m.imdb_id} -> tmdb={tmdb_id}")
                else:
                    m.tmdb_id = tmdb_id
                    m.save(update_fields=["tmdb_id"])
                fixed += 1
            else:
                skipped += 1

            time.sleep(opts["sleep"])

        msg = f"Done. fixed={fixed}, skipped={skipped}"
        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("[DRY] " + msg))
            raise CommandError("Dry-run rollback")
        else:
            self.stdout.write(self.style.SUCCESS(msg))
