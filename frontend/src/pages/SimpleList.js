import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchJson } from "../lib/api";
import Card from "../components/Card";
import Poster from "../components/Poster";
import StarBar from "../components/StarBar";

export default function SimpleList({ apiBase, title, path }) {
  const [state, setState] = useState({ loading: true, error: null, items: [] });
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setState({ loading: true, error: null, items: [] });
        const data = await fetchJson(`${apiBase}${path}`);
        setState({ loading: false, error: null, items: data });
      } catch (e) {
        if (!alive) return; setState({ loading: false, error: e.message, items: [] });
      }
    })();
    return () => { alive = false; };
  }, [apiBase, path]);

  return (
    <div className="grid gap-4">
      <h2 className="text-xl font-semibold">{title}</h2>
      {state.loading && <Card className="p-4 text-sm text-zinc-400">Loading…</Card>}
      {state.error && <Card className="p-4 text-sm text-red-400">Error: {state.error}</Card>}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {state.items.map(m => (
          <Link key={m.id} to={`/movie/${m.slug}`} className="group">
            <Card className="overflow-hidden">
              <Poster src={m.poster_url} alt={m.title} className="h-64 w-full object-cover" />
              <div className="p-3">
                <div className="line-clamp-1 font-medium group-hover:text-indigo-400">{m.title}</div>
                <div className="mt-0.5 text-xs text-zinc-400">{m.release_year ?? "—"}</div>
                <div className="mt-1 flex items-center justify-between">
                  <StarBar value={Number(m.avg_rating || 0)} />
                  <span className="text-[10px] text-zinc-500">{m.rating_count ?? 0} ratings</span>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}