import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Avg, Count

User = get_user_model()

def imdb_variants(raw):
    """Return common IMDb id variants for matching."""
    if not raw:
        return []
    s = str(raw).strip()
    z7 = s.zfill(7)                  # 114709 -> 0114709
    tt = f"tt{z7}"                   # -> tt0114709
    return list(dict.fromkeys([s, z7, tt]))

class Command(BaseCommand):
    help = "Import MovieLens ratings.csv and tags.csv using links.csv to map to api.Movie (tmdb_id/imdb_id)."

    def add_arguments(self, parser):
        base = Path(settings.BASE_DIR)
        parser.add_argument("--app", type=str, default="api")
        parser.add_argument("--links",   type=str, default=str(base / "api" / "data" / "links.csv"))
        parser.add_argument("--ratings", type=str, default=str(base / "api" / "data" / "ratings.csv"))
        parser.add_argument("--tags",    type=str, default=str(base / "api" / "data" / "tags.csv"))
        parser.add_argument("--limit",   type=int, default=None)
        parser.add_argument("--commit-every", type=int, default=5000)

    def handle(self, *args, **o):
        app_label   = o["app"]
        links_path  = Path(o["links"])
        ratings_path= Path(o["ratings"])
        tags_path   = Path(o["tags"])
        limit       = o["limit"]
        batch_n     = o["commit_every"]

        Movie   = apps.get_model(app_label, "Movie")
        Rating  = apps.get_model(app_label, "Rating")
        Tag     = apps.get_model(app_label, "Tag")
        Tagging = apps.get_model(app_label, "Tagging")

        # --- Build lookup maps for tmdb/imdb -> Movie.pk
        self.stdout.write(self.style.NOTICE("Building tmdb_id/imdb_id → Movie.pk maps…"))
        tmdb_to_pk = dict(Movie.objects.exclude(tmdb_id__isnull=True).values_list("tmdb_id", "pk"))
        imdb_to_pk = dict(Movie.objects.exclude(imdb_id__isnull=True).values_list("imdb_id", "pk"))

        if not links_path.exists():
            raise CommandError(f"links.csv not found: {links_path}")

        # Map MovieLens movieId -> Movie.pk via links.csv
        self.stdout.write(self.style.NOTICE(f"Reading links from {links_path}"))
        movieid_to_pk, unmatched = {}, 0
        with links_path.open(newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            req = {"movieId", "imdbId", "tmdbId"}
            if not req.issubset(rdr.fieldnames or []):
                raise CommandError(f"links.csv must have columns: {req}")
            for rec in rdr:
                try:
                    ml_mid = int(rec["movieId"])
                except Exception:
                    continue
                pk = None
                # Try tmdb first (stored as integer in links; Movie.tmdb_id is IntegerField)
                tmdb_raw = (rec.get("tmdbId") or "").strip()
                if tmdb_raw:
                    try:
                        pk = tmdb_to_pk.get(int(tmdb_raw))
                    except Exception:
                        pk = None
                # Fallback via imdb
                if not pk:
                    for cand in imdb_variants(rec.get("imdbId")):
                        pk = imdb_to_pk.get(cand)
                        if pk:
                            break
                if pk:
                    movieid_to_pk[ml_mid] = pk
                else:
                    unmatched += 1

        self.stdout.write(self.style.SUCCESS(f"links map: {len(movieid_to_pk)} matched, {unmatched} unmatched"))
        if not movieid_to_pk:
            raise CommandError("No movieId mapped → Movie.pk. Ensure your Movie rows have tmdb_id and/or imdb_id set and links.csv is correct.")

        # Simple caches
        user_cache, tag_cache = {}, {}

        def get_user_pk(uid: int):
            if uid in user_cache:
                return user_cache[uid]
            u, _ = User.objects.get_or_create(username=f"u{uid}", defaults={"email": f"u{uid}@example.com"})
            user_cache[uid] = u.pk
            return u.pk

        def get_tag_pk(name: str):
            name = (name or "").strip()
            if not name:
                return None
            if name in tag_cache:
                return tag_cache[name]
            t, _ = Tag.objects.get_or_create(name=name)
            tag_cache[name] = t.pk
            return t.pk

        # --- Import ratings.csv (Rating.rating Decimal) ---
        if ratings_path.exists():
            self.stdout.write(self.style.MIGRATE_HEADING(f"Importing ratings from {ratings_path}"))
            total = done = skipped = 0
            with ratings_path.open(newline="", encoding="utf-8") as fh:
                rdr = csv.DictReader(fh)
                req = {"userId", "movieId", "rating", "timestamp"}
                if not req.issubset(rdr.fieldnames or []):
                    raise CommandError(f"ratings.csv must have columns: {req}")
                with transaction.atomic():
                    for rec in rdr:
                        total += 1
                        if limit and total > limit:
                            break
                        try:
                            ml_mid = int(rec["movieId"])
                            pk = movieid_to_pk.get(ml_mid)
                            if not pk:
                                skipped += 1
                                continue
                            upk = get_user_pk(int(rec["userId"]))
                            try:
                                score = Decimal(str(rec["rating"]))
                            except (InvalidOperation, TypeError):
                                skipped += 1
                                continue
                            # Idempotent: one rating per (movie,user)
                            Rating.objects.update_or_create(
                                movie_id=pk, user_id=upk,
                                defaults={"rating": score}  # no timestamp fields to set
                            )
                            done += 1
                            if done and done % batch_n == 0:
                                transaction.set_autocommit(True); transaction.set_autocommit(False)
                                self.stdout.write(f"  ratings imported: {done}…")
                        except Exception:
                            skipped += 1
                            continue
            self.stdout.write(self.style.SUCCESS(f"ratings: imported/updated {done}, skipped {skipped}, total {total}"))
        else:
            self.stdout.write(self.style.WARNING(f"ratings.csv not found: {ratings_path} (skipping)"))

        # --- Import tags.csv into Tagging (preserve user+tag) ---
        if tags_path.exists():
            self.stdout.write(self.style.MIGRATE_HEADING(f"Importing tags from {tags_path}"))
            total = done = skipped = 0
            with tags_path.open(newline="", encoding="utf-8") as fh:
                rdr = csv.DictReader(fh)
                req = {"userId", "movieId", "tag", "timestamp"}
                if not req.issubset(rdr.fieldnames or []):
                    raise CommandError(f"tags.csv must have columns: {req}")
                with transaction.atomic():
                    for rec in rdr:
                        total += 1
                        if limit and total > limit:
                            break
                        try:
                            ml_mid = int(rec["movieId"])
                            pk = movieid_to_pk.get(ml_mid)
                            if not pk:
                                skipped += 1
                                continue
                            upk = get_user_pk(int(rec["userId"]))
                            tpk = get_tag_pk(rec.get("tag"))
                            if not tpk:
                                skipped += 1
                                continue
                            # unique_together (movie,user,tag)
                            Tagging.objects.update_or_create(
                                movie_id=pk, user_id=upk, tag_id=tpk, defaults={}
                            )
                            done += 1
                            if done and done % batch_n == 0:
                                transaction.set_autocommit(True); transaction.set_autocommit(False)
                                self.stdout.write(f"  taggings imported: {done}…")
                        except Exception:
                            skipped += 1
                            continue
            self.stdout.write(self.style.SUCCESS(f"taggings: imported/updated {done}, skipped {skipped}, total {total}"))
        else:
            self.stdout.write(self.style.WARNING(f"tags.csv not found: {tags_path} (skipping)"))

        # --- Recalculate Movie.avg_rating & rating_count from Rating.rating ---
        self.stdout.write(self.style.MIGRATE_HEADING("Recalculating avg_rating / rating_count…"))
        to_update = []
        for m in Movie.objects.all().annotate(a=Avg("ratings__rating"), c=Count("ratings")):
            new_avg = float(round((m.a or 0), 2))
            new_cnt = int(m.c or 0)
            if m.avg_rating != new_avg or m.rating_count != new_cnt:
                m.avg_rating = new_avg
                m.rating_count = new_cnt
                to_update.append(m)
        if to_update:
            Movie.objects.bulk_update(to_update, ["avg_rating", "rating_count"], batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"updated {len(to_update)} movies"))
        self.stdout.write(self.style.SUCCESS("Done."))

