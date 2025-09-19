import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { fetchJson } from "../lib/api";
import { useDebounce } from "../lib/hooks";
import { joinQS, useQuery } from "../lib/utils";
import Poster from "../components/Poster";
import StarBar from "../components/StarBar";
import Card from "../components/Card";
import Input from "../components/Input";
import Chip from "../components/Chip";
import Button from "../components/Button";

export default function Browse({ apiBase }) {
  const navigate = useNavigate();
  const q = useQuery();
  const [title, setTitle] = useState(q.get("title") || "");
  const [genre, setGenre] = useState(q.get("genre") || "");
  const [tag, setTag] = useState(q.get("tag") || "");
  const [minYear, setMinYear] = useState(q.get("min_year") || "");
  const [maxYear, setMaxYear] = useState(q.get("max_year") || "");
  const [minRating, setMinRating] = useState(q.get("min_rating") || "");
  const [page, setPage] = useState(Number(q.get("page") || 1));

  const debTitle = useDebounce(title, 400);
  const params = useMemo(() => ({ title: debTitle, genre, tag, min_year: minYear, max_year: maxYear, min_rating: minRating, page }), [debTitle, genre, tag, minYear, maxYear, minRating, page]);
  const [state, setState] = useState({ loading: true, error: null, data: null });

  useEffect(() => {
    const qs = joinQS(params);
    navigate(`/browse?${qs}`, { replace: true });
  }, [params]);

  useEffect(() => {
    let isCancelled = false;
    async function run() {
      setState(s => ({ ...s, loading: true, error: null }));
      try {
        const url = `${apiBase}/movies/?${joinQS(params)}`;
        const data = await fetchJson(url);
        if (!isCancelled) setState({ loading: false, error: null, data });
      } catch (e) {
        if (!isCancelled) setState({ loading: false, error: e.message, data: null });
      }
    }
    run();
    return () => { isCancelled = true; };
  }, [apiBase, params]);

  const results = state.data?.results || state.data || [];
  const count = state.data?.count ?? results.length;

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 space-y-6">
      <Card >
        <div>
          <div className="col-span-2 md:col-span-2">
            <label className="mb-1 text-white bg-black">Title</label>
            <Input value={title} onChange={e => { setTitle(e.target.value); setPage(1); }} placeholder="search title…" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-zinc-400">Genre</label>
            <Input value={genre} onChange={e => { setGenre(e.target.value); setPage(1); }} placeholder="e.g. Action" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-zinc-400">Tag</label>
            <Input value={tag} onChange={e => { setTag(e.target.value); setPage(1); }} placeholder="e.g. classic" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-zinc-400">Min Year</label>
            <Input value={minYear} onChange={e => { setMinYear(e.target.value); setPage(1); }} placeholder="1990" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-zinc-400">Max Year</label>
            <Input value={maxYear} onChange={e => { setMaxYear(e.target.value); setPage(1); }} placeholder="2025" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-zinc-400">Min Rating</label>
            <Input value={minRating} onChange={e => { setMinRating(e.target.value); setPage(1); }} placeholder="3.5" />
          </div>
        </div>
      </Card>

      {state.loading && <Card className="p-6 text-sm text-zinc-400">Loading…</Card>}
      {state.error && <Card className="p-6 text-sm text-red-400">Error: {state.error}</Card>}

      {!state.loading && !state.error && (
        <div className = "bg-black text-white p-4 rounded-lg">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
            {results.map((m) => (
              <Link key={m.id} to={`/movie/${m.slug}`} className="group">
                <Card className="overflow-hidden">
                  <Poster src={m.poster_url} alt={m.title} className="h-40 w-full object-cover" />
                  <div className="p-3">
                    <div className="line-clamp-1 font-medium group-hover:text-indigo-400">{m.title}</div>
                    <div className="mt-0.5 text-xs text-zinc-400">{m.release_year ?? "—"}</div>
                    <div className="mt-1 flex items-center justify-between">
                      <StarBar value={Number(m.avg_rating || 0)} />
                      <span className="text-[10px] text-zinc-500">{m.rating_count ?? 0} ratings</span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {(m.genres || []).slice(0, 2).map(g => <Chip key={g.id}>{g.name}</Chip>)}
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <div className="text-xs text-zinc-500">Total: {count}</div>
            <div className="flex items-center gap-2">
              <Button variant="secondary" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>Prev</Button>
              <span className="text-sm">Page {page}</span>
              <Button variant="secondary" onClick={() => setPage(p => p + 1)} disabled={results.length === 0}>Next</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}