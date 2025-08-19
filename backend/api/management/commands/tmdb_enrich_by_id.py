import os, time, requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Movie, Genre, Person, MovieCast

API_KEY = os.getenv("TMDB_API_KEY", "feda2c7c12b2a9fbbea6a861c1367e30")
BASE = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

def _get(path, **params):
    if not API_KEY:
        raise CommandError("TMDB_API_KEY not set in environment")
    params["api_key"] = API_KEY
    r = requests.get(f"{BASE}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_detail_and_credits(tmdb_id: str, with_credits: bool):
    if with_credits:
        # one call for details, one for credits (keeps payload small & simple)
        dt = _get(f"/movie/{tmdb_id}", append_to_response="external_ids")
        cr = _get(f"/movie/{tmdb_id}/credits")
        return dt, cr
    else:
        dt = _get(f"/movie/{tmdb_id}", append_to_response="external_ids")
        return dt, None
    
FIND_URL = f"{BASE}/find/{{external_id}}"
SEARCH_URL = f"{BASE}/search/movie"

def tmdb_find_by_imdb(imdb_id):
    if not imdb_id: return None
    r = requests.get(FIND_URL.format(external_id=imdb_id),
                     params={"api_key": API_KEY, "external_source": "imdb_id"}, timeout=15)
    r.raise_for_status()
    res = r.json().get("movie_results", [])
    return str(res[0]["id"]) if res else None

def tmdb_search_by_title_year(title, year=None):
    if not title: return None
    params = {"api_key": API_KEY, "query": title}
    if year: params["year"] = year
    r = requests.get(SEARCH_URL, params=params, timeout=15)
    r.raise_for_status()
    res = r.json().get("results", [])
    return str(res[0]["id"]) if res else None


class Command(BaseCommand):
    help = "Enrich Movie rows from TMDb using tmdb_id (details, genres, poster; optional credits)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Limit number of movies to process")
        parser.add_argument("--sleep", type=float, default=0.25, help="Seconds to sleep between movies")
        parser.add_argument("--refresh", action="store_true",
                            help="Overwrite non-empty fields (default only fills missing)")
        parser.add_argument("--credits", action="store_true",
                            help="Also import cast/crew into Person/MovieCast")
        parser.add_argument("--only_missing", action="store_true",
                            help="Only fill fields that are empty; don't overwrite existing data")

    @transaction.atomic
    def handle(self, *args, **opts):
        only_missing = not opts["refresh"]
        with_credits = opts["credits"]
        sleep = opts["sleep"]

        qs = (Movie.objects
              #.exclude(tmdb_id__isnull=True)
              #.exclude(tmdb_id="")
              .filter(poster_url__isnull=True)
              .order_by("movieId"))
        if opts["limit"]:
            qs = qs[:opts["limit"]]

        updated, skipped = 0, 0
        for m in qs:
            try:
                dt, cr = fetch_detail_and_credits(m.imdb_id, with_credits)

                # ----- details -----
                poster_path = dt.get("poster_path")
                poster_url = f"{IMG_BASE}{poster_path}" if poster_path else None
                overview = (dt.get("overview") or "").strip()
                release_date = (dt.get("release_date") or "").strip()
                imdb_id = (dt.get("external_ids") or {}).get("imdb_id")

                fields = []
                if only_missing:
                    if not m.overview and overview:
                        m.overview = overview; fields.append("overview")
                    if not m.poster_url and poster_url:
                        m.poster_url = poster_url; fields.append("poster_url")
                    if not m.imdb_id and imdb_id:
                        m.imdb_id = imdb_id; fields.append("imdb_id")
                    if not m.year and release_date:
                        try:
                            m.year = int(release_date[:4]); fields.append("year")
                        except Exception:
                            pass
                else:  # refresh (overwrite)
                    m.overview = overview; fields.append("overview")
                    if poster_url:
                        m.poster_url = poster_url; fields.append("poster_url")
                    if imdb_id:
                        m.imdb_id = imdb_id; fields.append("imdb_id")
                    if release_date:
                        try:
                            m.year = int(release_date[:4]); fields.append("year")
                        except Exception:
                            pass

                if fields:
                    m.save(update_fields=list(set(fields)))  # de-dupe for safety

                # ----- genres (M2M) -----
                tmdb_genres = dt.get("genres") or []
                for g in tmdb_genres:
                    gobj, _ = Genre.objects.get_or_create(
                        tmdb_id=g.get("id"),
                        defaults={"name": g.get("name") or str(g.get("id"))}
                    )
                    # If name arrives later, ensure it’s set
                    if not gobj.name and g.get("name"):
                        gobj.name = g["name"]; gobj.save(update_fields=["name"])
                    m.genres.add(gobj)

                # ----- credits -----
                if with_credits and cr:
                    # cast
                    for c in (cr.get("cast") or []):
                        p = self._get_or_create_person(c)
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

                updated += 1
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    self.stderr.write(f"TMDb ID {m.tmdb_id} not found (404); skipping")
                    skipped += 1
                    
                    
            except requests.HTTPError as e:
                self.stderr.write(f"HTTP {e.response.status_code} for movieId={m.movieId} (tmdb_id={m.tmdb_id})")
                skipped += 1
            except Exception as e:
                self.stderr.write(f"Error on movieId={m.movieId}: {e}")
                skipped += 1
            time.sleep(sleep)

        self.stdout.write(self.style.SUCCESS(f"Enriched {updated} movies; skipped {skipped}"))

    def _get_or_create_person(self, cdict):
        tmdb_pid = cdict.get("id")
        name = cdict.get("name") or ""
        profile_path = cdict.get("profile_path")
        profile_url = f"{IMG_BASE}{profile_path}" if profile_path else None

        if tmdb_pid is not None:
            p, _ = Person.objects.get_or_create(
                tmdb_id=str(tmdb_pid),
                defaults={"name": name, "profile_url": profile_url},
            )
            # Update if new info arrives
            to_update = []
            if name and p.name != name:
                p.name = name; to_update.append("name")
            if profile_url and p.profile_url != profile_url:
                p.profile_url = profile_url; to_update.append("profile_url")
            if to_update: p.save(update_fields=to_update)
            return p

        # Fallback if TMDb person id missing (rare)
        p, _ = Person.objects.get_or_create(name=name, defaults={"profile_url": profile_url})
        if profile_url and p.profile_url != profile_url:
            p.profile_url = profile_url; p.save(update_fields=["profile_url"])
        return p
