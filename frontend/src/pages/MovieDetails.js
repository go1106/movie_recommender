import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchJson } from "../lib/api";
import Card from "../components/Card";
import Poster from "../components/Poster";
import StarBar from "../components/StarBar";
import Chip from "../components/Chip";
import MovieActions from "../components/MovieActions";






export default function MovieDetail({ apiBase }) {
  const { slug } = useParams();
  const [state, setState] = useState({ loading: true, error: null, movie: null });
  const [mlt, setMlt] = useState({ loading: true, error: null, items: [] });



  const fetchMovie = useCallback(async () => {
    setState(s => ({ ...s, loading: true, error: null }));
    try {
      const movie = await fetchJson(`${apiBase}/movies/${slug}/`);
      setState({ loading: false, error: null, movie });
    } catch (e) {
      setState({ loading: false, error: String(e), movie: null });
    }
  }, [apiBase, slug]);

  useEffect(() => { fetchMovie(); }, [fetchMovie]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setState(s => ({ ...s, loading: true, error: null }));
        const movie = await fetchJson(`${apiBase}/movies/${slug}/`);
        if (!alive) return;
        setState({ loading: false, error: null, movie });
      } catch (e) {
        if (!alive) return; setState({ loading: false, error: e.message, movie: null });
      }
    })();
    return () => { alive = false; };
  }, [apiBase, slug]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setMlt({ loading: true, error: null, items: [] });
        const items = await fetchJson(`${apiBase}/movies/${slug}/more_like_this/`);
        if (!alive) return;
        setMlt({ loading: false, error: null, items });
      } catch (e) {
        if (!alive) return; setMlt({ loading: false, error: e.message, items: [] });
      }
    })();
    return () => { alive = false; };
  }, [apiBase, slug]);

  if (state.loading) return <Card className="p-6 text-sm text-zinc-400">Loading…</Card>;
  if (state.error) return <Card className="p-6 text-sm text-red-400">Error: {state.error}</Card>;
  const m = state.movie;

  return (
    <div className="grid gap-6 md:grid-cols-[280px_1fr]">
      <Card className="overflow-hidden">
        <Poster src={m.poster_url} alt={m.title} className="h-full w-full object-cover" />
      </Card>
      <div className="grid gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{m.title} <span className="text-zinc-400">({m.release_year ?? "—"})</span></h1>
          <div className="mt-2 flex items-center gap-3 text-sm">
            <StarBar value={Number(m.avg_rating || 0)} />
            <span className="text-zinc-400">{m.rating_count ?? 0} ratings</span>
            {m.runtime ? <span className="text-zinc-500">• {m.runtime} min</span> : null}
          </div>
        </div>
        <div className="text-sm text-zinc-300">
          <p className="whitespace-pre-line">{m.overview || "No overview."}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {(m.genres || []).map(g => <Chip key={g.id}>{g.name}</Chip>)}
            {(m.tags || []).slice(0, 6).map(t => <Chip key={t.id}>{t.name}</Chip>)}
          </div>
        </div>
        <div>
                  {/* NEW: Actions */}
          
          <MovieActions apiBase={apiBase} movieId={m.id} onChanged={fetchMovie} />

                  {/* Overview / tags */}
          <div className="text-sm text-zinc-300">
              <p className="whitespace-pre-line">{m.overview || "No overview."}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {(m.genres || []).map(g => <Chip key={g.id}>{g.name}</Chip>)}
                {(m.tags || []).slice(0, 10).map(t => <Chip key={t.id || t}>{t.name || t}</Chip>)}
              </div>
          </div>




        </div>
        <div>
          <h3 className="mb-2 font-semibold">Cast</h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {(m.cast || []).map((c, i) => (
              <Card key={`${c.name}-${i}`} className="p-3">
                <div className="line-clamp-1 font-medium">{c.name || "Unknown"}</div>
                <div className="line-clamp-1 text-xs text-zinc-400">{c.character || c.job || ""}</div>
              </Card>
            ))}
          </div>
        </div>
        <div>
          <h3 className="mb-2 font-semibold">More like this</h3>
          {mlt.loading && <Card className="p-4 text-sm text-zinc-400">Loading…</Card>}
          {mlt.error && <Card className="p-4 text-sm text-red-400">Error: {mlt.error}</Card>}
          {!mlt.loading && !mlt.error && (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
              {mlt.items.map(item => (
                <Link key={item.id} to={`/movie/${item.slug}`} className="group">
                  <Card className="overflow-hidden">
                    <Poster src={item.poster_url} alt={item.title} className="h-48 w-full object-cover" />
                    <div className="p-3">
                      <div className="line-clamp-1 font-medium group-hover:text-indigo-400">{item.title}</div>
                      <div className="mt-0.5 text-xs text-zinc-400">{item.release_year ?? "—"}</div>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}



