from django.core.management.base import BaseCommand
from django.db import transaction
import pandas as pd
from api.models import Movie, Tag, MovieTag

class Command(BaseCommand):
    help = 'Load links.cvs(movieId, imdbId,tmdbId) and tags.csv(userId,movieId,tag) into the database'

    def add_arguments(self, parser):
        parser.add_argument("--links", type=str, default="api/data/links.csv")
        parser.add_argument("--tags",  type=str, default="api/data/tags.csv")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        ctx = transaction.atomic if not dry_run else _NoopTxn

        with ctx():
            if opts.get("links"):
                self._import_links(opts["links"])
            if opts.get("tags"):
                self._import_tags(opts["tags"])

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run complete — no changes written."))

    # ---------- LINKS ----------
    def _import_links(self, path: str):
        self.stdout.write(self.style.NOTICE(f"Importing links from {path}"))

        # keep as strings; handle BOM; normalize columns
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
        df.columns = [c.strip().lower() for c in df.columns]
        required = {"movieid", "imdbid", "tmdbid"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"links.csv missing required columns: {sorted(missing)}")

        updated, missing_movies = 0, 0
        for _, row in df.iterrows():
            movieid = (row.get("movieid") or "").strip()
            imdbid  = (row.get("imdbid")  or "").strip()
            tmdbid  = (row.get("tmdbid")  or "").strip()

            if not movieid:
                continue

            movie = Movie.objects.filter(movieId=int(movieid)).first()
            if not movie:
                missing_movies += 1
                continue

            fields_to_update = []

            # IMDb ids may be plain digits; normalize to start with 'tt'
            if imdbid:
                norm = imdbid if imdbid.startswith("tt") else f"tt{imdbid}"
                if movie.imdb_id != norm:
                    movie.imdb_id = norm
                    fields_to_update.append("imdb_id")

            # TMDB id should be integer if present
            if tmdbid and tmdbid.isdigit():
                val = int(tmdbid)
                if movie.tmdb_id != val:
                    movie.tmdb_id = val
                    fields_to_update.append("tmdb_id")

            if fields_to_update:
                movie.save(update_fields=fields_to_update)
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Links: updated {updated}, missing movies {missing_movies}"
        ))

    # ---------- TAGS ----------
    def _import_tags(self, path: str):
        self.stdout.write(self.style.NOTICE(f"Importing tags from {path}"))

        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
        df.columns = [c.strip().lower() for c in df.columns]
        required = {"userid", "movieid", "tag"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"tags.csv missing required columns: {sorted(missing)}")

        created_links, skipped = 0, 0
        for _, row in df.iterrows():
            user   = (row.get("userid")  or "").strip()
            movieid= (row.get("movieid") or "").strip()
            tagstr = (row.get("tag")     or "").strip()

            if not (user and movieid and tagstr):
                skipped += 1
                continue

            movie = Movie.objects.filter(movieId=int(movieid)).first()
            if not movie:
                skipped += 1
                continue

            tag, _ = Tag.objects.get_or_create(name=tagstr)
            # through-model stores who tagged which movie
            obj, created = MovieTag.objects.get_or_create(
                movie=movie, tag=tag, userId=int(user)
            )
            created_links += int(created)

        self.stdout.write(self.style.SUCCESS(
            f"User tags: created {created_links}, skipped {skipped}"
        ))

class _NoopTxn:
    def __enter__(self): return self
    def __exit__(self, *a): return False