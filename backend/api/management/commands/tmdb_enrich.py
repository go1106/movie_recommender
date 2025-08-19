import os, time, requests
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Movie, Genre, Person, MovieCast

API_KEY = os.getenv("TMDB_API_KEY", "")
BASE = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

def _get(url, **params):
    params["api_key"] = API_KEY
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def movie_detail(tmdb_id):
    return _get(f"{BASE}/movie/{tmdb_id}", append_to_response="external_ids")

def movie_credits(tmdb_id):
    return _get(f"{BASE}/movie/{tmdb_id}/credits")

def movie_watch_providers(tmdb_id):
    return _get(f"{BASE}/movie/{tmdb_id}/watch/providers")

def first_nonempty(*vals):
    for v in vals:
        if v not in (None, "", []): return v
    return None

class Command(BaseCommand):
    help = "Enrich Movie rows from TMDB (details, genres, poster) and import cast/crew."

    def add_arguments(self, parser):
        parser.add_argument("--only-missing", action="store_true",
                            help="Only fill fields that are empty; don't overwrite")
        parser.add_argument("--refresh", action="store_true",
                            help="Overwrite existing non-empty fields")
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--sleep", type=float, default=0.25)
        parser.add_argument("--credits", action="store_true",
                            help="Also fetch people + credits")
        parser.add_argument("--providers", action="store_true",
                            help="Fetch watch providers (stub; requires Provider model if you add one)")

    @transaction.atomic
    def handle(self, *args, **opts):
        assert API_KEY, "TMDB_API_KEY not set"
        over = opts["refresh"]
        only_missing = opts["only-missing"] and not over
        qs = Movie.objects.exclude(tmdb_id__isnull=True).exclude(tmdb_id="").order_by("movieId")
        if opts["limit"]: qs = qs[:opts["limit"]]
        updated, skipped = 0, 0

        for m in qs:
            try:
                dt = movie_detail(m.tmdb_id)
                # ----- details -----
                poster_path = dt.get("poster_path")
                poster_url = f"{IMG_BASE}{poster_path}" if poster_path else None
                overview = dt.get("overview") or ""
                release_date = dt.get("release_date") or ""
                runtime = dt.get("runtime")
                imdb_id = (dt.get("external_ids") or {}).get("imdb_id")

                # update fields respecting flags
                fields = []
                if over or (only_missing and not m.overview):
                    m.overview = overview; fields.append("overview")
                if over or (only_missing and not m.poster_url):
                    if poster_url:
                        m.poster_url = poster_url; fields.append("poster_url")
                if over or (only_missing and not m.imdb_id):
                    if imdb_id:
                        m.imdb_id = imdb_id; fields.append("imdb_id")
                # year from release_date if missing
                if (over or (only_missing and not m.year)) and release_date:
                    y = int(release_date[:4])
                    m.year = y; fields.append("year")

                if fields:
                    m.save(update_fields=fields)

                # ----- genres (M2M) -----
                tmdb_genres = dt.get("genres") or []
                for g in tmdb_genres:
                    gobj, _ = Genre.objects.get_or_create(
                        tmdb_id=g.get("id"), defaults={"name": g.get("name") or str(g.get("id"))}
                    )
                    # if name came later, ensure name is set
                    if not gobj.name and g.get("name"):
                        gobj.name = g["name"]; gobj.save(update_fields=["name"])
                    m.genres.add(gobj)

                # ----- credits -----
                if opts["credits"]:
                    cr = movie_credits(m.tmdb_id)
                    # cast
                    for c in (cr.get("cast") or []):
                        p = self._get_or_create_person(c)
                        # upsert MovieCast cast role
                        MovieCast.objects.get_or_create(
                            movie=m, person=p, role_type="cast", job="",
                            defaults={"character": c.get("character") or "", "order": c.get("order") or 999}
                        )
                    # crew
                    for c in (cr.get("crew") or []):
                        p = self._get_or_create_person(c)
                        MovieCast.objects.get_or_create(
                            movie=m, person=p, role_type="crew", job=c.get("job") or "",
                            defaults={"character": "", "order": c.get("order") or 999}
                        )

                # (optional) providers
                if opts["providers"]:
                    _ = movie_watch_providers(m.tmdb_id)  # you can extend later to a Provider model

                updated += 1
                time.sleep(opts["sleep"])
            except requests.HTTPError as e:
                self.stderr.write(f"HTTP {e.response.status_code} for movieId={m.movieId} tmdb_id={m.tmdb_id}")
                skipped += 1
            except Exception as e:
                self.stderr.write(f"Error on movieId={m.movieId}: {e}")
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f"Enriched {updated} movies; skipped {skipped}"))

    def _get_or_create_person(self, cdict):
        """Create/find Person by tmdb_id if present; fallback to name."""
        tmdb_pid = cdict.get("id")
        name = cdict.get("name") or ""
        profile_path = cdict.get("profile_path")
        profile_url = f"{IMG_BASE}{profile_path}" if profile_path else None

        if tmdb_pid is not None:
            p, created = Person.objects.get_or_create(
                tmdb_id=str(tmdb_pid),
                defaults={"name": name, "profile_url": profile_url},
            )
            # update profile/name if we got better data
            to_update = []
            if not p.name and name:
                p.name = name; to_update.append("name")
            if profile_url and p.profile_url != profile_url:
                p.profile_url = profile_url; to_update.append("profile_url")
            if to_update: p.save(update_fields=to_update)
            return p

        # fallback on name (less reliable)
        p, _ = Person.objects.get_or_create(name=name, defaults={"profile_url": profile_url})
        if profile_url and p.profile_url != profile_url:
            p.profile_url = profile_url; p.save(update_fields=["profile_url"])
        return p
