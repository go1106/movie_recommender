import os, time, requests
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Movie

API_KEY = os.getenv("TMD_API_KEY", "feda2c7c12b2a9fbbea6a861c1367e30")
BASE = "https://api.themoviedb.org/3"

def tmdb_search(title, year=None):
    params = {"api_key": API_KEY, "query": title}
    if year: params["year"] = year
    r = requests.get(f"{BASE}/search/movie", params=params, timeout=15)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None

class Command(BaseCommand):
    help = "Find and store tmdb_id for movies missing it via title/year."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--sleep", type=float, default=0.25)  # TMDB rate limit friendly

    @transaction.atomic
    def handle(self, *args, **opts):
        assert API_KEY, "TMDB_API_KEY not set"
        qs = Movie.objects.filter(tmdb_id__isnull=True).order_by("movieId")
        if opts["limit"]: qs = qs[:opts["limit"]]
        linked = 0
        for m in qs:
            hit = tmdb_search(m.title, m.year)
            if hit:
                m.tmdb_id = str(hit["id"])
                m.save(update_fields=["tmdb_id"])
                linked += 1
            time.sleep(opts["sleep"])
        self.stdout.write(self.style.SUCCESS(f"Linked {linked} movies with tmdb_id"))
