# app/management/commands/ingest_movies.py
import csv, time
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from app.models import Movie  # adjust import
import requests

TMDB_KEY = "feda2c7c12b2a9fbbea6a861c1367e30"
TMDB_SEARCH = "https://api.themoviedb.org/3/search/movie"
TMDB_DETAIL = "https://api.themoviedb.org/3/movie/{id}"

def tmdb_search(title, year=None):
    params = {"api_key": TMDB_KEY, "query": title}
    if year:
        params["year"] = year
    r = requests.get(TMDB_SEARCH, params=params, timeout=15)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None

def tmdb_detail(tmdb_id):
    r = requests.get(TMDB_DETAIL.format(id=tmdb_id), params={"api_key": TMDB_KEY}, timeout=15)
    r.raise_for_status()
    return r.json()

class Command(BaseCommand):
    help = "Ingest CSV and enrich from TMDB; idempotent upsert by tmdb_id or (title,year)."

    def add_arguments(self, parser):
        parser.add_argument("--csv", required=True)
        parser.add_argument("--refresh", action="store_true", help="Overwrite existing non-empty fields")
        parser.add_argument("--limit", type=int, default=0, help="Limit rows (for testing)")

    @transaction.atomic
    def handle(self, *args, **opts):
        csv_path = Path(opts["csv"])
        if not csv_path.exists():
            raise CommandError(f"CSV not found: {csv_path}")

        count = 0
        failed = []

        with csv_path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = (row.get("title") or "").strip()
                if not title:
                    failed.append({"reason": "missing title", **row})
                    continue
                try:
                    year = row.get("release_year")
                    year = int(year) if year and str(year).isdigit() else None
                    tmdb_id = row.get("tmdb_id")
                    if tmdb_id:
                        tmdb_id = int(str(tmdb_id).strip()) if str(tmdb_id).strip().isdigit() else None

                    # Resolve missing tmdb_id
                    if not tmdb_id:
                        hit = tmdb_search(title, year)
                        if hit:
                            tmdb_id = hit["id"]
                            time.sleep(0.2)  # gentle rate limit

                    # Upsert movie by tmdb_id if available, else by (title, year)
                    lookup = {"tmdb_id": tmdb_id} if tmdb_id else {"title": title, "release_year": year}
                    movie, created = Movie.objects.get_or_create(**lookup)

                    # Enrich from TMDB if we have an id
                    overview = row.get("overview", "") or ""
                    poster_url = row.get("poster_url", "") or ""
                    if tmdb_id:
                        dt = tmdb_detail(tmdb_id)
                        time.sleep(0.2)
                        overview_api = dt.get("overview") or ""
                        poster_api = dt.get("poster_path")
                        poster_api = f"https://image.tmdb.org/t/p/w500{poster_api}" if poster_api else ""
                        # choose source: keep non-empty value unless --refresh
                        overview = (overview_api or overview) if (opts["refresh"] or not movie.overview) else movie.overview or overview or overview_api
                        poster_url = (poster_api or poster_url) if (opts["refresh"] or not movie.poster_url) else movie.poster_url or poster_url or poster_api

                    # Update fields
                    movie.title = title if (opts["refresh"] or not movie.title) else movie.title
                    movie.release_year = year or movie.release_year
                    if overview:
                        movie.overview = overview
                    if poster_url:
                        movie.poster_url = poster_url
                    # example: tags from CSV (comma-separated)
                    tags = (row.get("tags") or "").strip()
                    if tags:
                        movie.tags = tags

                    movie.slug = movie.slug or slugify(f"{title}-{year or ''}")[:80]
                    movie.save()
                    count += 1

                    if opts["limit"] and count >= opts["limit"]:
                        break

                except Exception as e:
                    failed.append({"reason": str(e), **row})

        self.stdout.write(self.style.SUCCESS(f"Ingest complete. Upserted {count} movies. Failed: {len(failed)}"))
        if failed:
            # Write a small failure report
            out = csv_path.with_suffix(".failed.csv")
            with out.open("w", newline="") as g:
                w = csv.DictWriter(g, fieldnames=["reason"] + list(reader.fieldnames))
                w.writeheader()
                for r in failed:
                    w.writerow(r)
            self.stdout.write(self.style.WARNING(f"Wrote failures to {out}"))
