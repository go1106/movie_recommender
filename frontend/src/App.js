import React, { useEffect, useMemo, useRef, useState } from "react";
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate, useLocation } from "react-router-dom";

/**
 * Single‑file React app for your Django Movie API
 *
 * Features
 * - Configurable API base (persisted to localStorage)
 * - Browse list with search + filters + pagination (DRF style)
 * - Movie detail page (with cast) + "More like this"
 * - Trending & Top Rated shortcuts
 * - Simple Recs view by username using your RecCache endpoint
 *
 * Assumes Django endpoints:
 *   GET  /api/movies/?title=&min_year=&max_year=&min_rating=&genre=&tag=&page=
 *   GET  /api/movies/:slug/
 *   GET  /api/movies/:slug/more_like_this/
 *   GET  /api/trending/
 *   GET  /api/top-rated/
 *   GET  /api/rec-cache/:username/
 *
 * NOTE: Enable CORS on Django for local dev (see chat instructions).
 */

// ---------- helpers ----------
const ls = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v ?? fallback; } catch { return fallback; }
  },
  set(key, val) { try { localStorage.setItem(key, val); } catch {} }
};

function useDebounce(value, delay = 400) {
  const [v, setV] = useState(value);
  useEffect(() => { const t = setTimeout(() => setV(value), delay); return () => clearTimeout(t); }, [value, delay]);
  return v;
}

function useQuery() { return new URLSearchParams(useLocation().search); }

function joinQS(params) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") q.set(k, v);
  return q.toString();
}

function StarBar({ value = 0, size = 14 }) {
  // value: 0..5 (one decimal)
  const full = Math.floor(value);
  const half = value - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  const star = (ch, i) => <span key={i} style={{ fontSize: size, lineHeight: 1 }}>{ch}</span>;
  return (
    <span title={`${value.toFixed(1)} / 5`} className="inline-flex items-center gap-0.5">
      {[...Array(full)].map((_, i) => star("★", `f${i}`))}
      {half && star("☆", "h")}
      {[...Array(empty)].map((_, i) => star("✩", `e${i}`))}
    </span>
  );
}

function Poster({ src, alt, className = "" }) {
  const ph = "data:image/svg+xml;utf8," + encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' width='300' height='450'><rect width='100%' height='100%' fill='#111'/><text x='50%' y='50%' fill='#888' font-size='20' text-anchor='middle' dominant-baseline='middle'>No Poster</text></svg>`
  );
  return <img src={src || ph} alt={alt} className={className} />;
}

// ---------- API client ----------
function useApiBase() {
  const [apiBase, setApiBase] = useState(() => ls.get("apiBase", "http://127.0.0.1:8000/api"));
  useEffect(() => ls.set("apiBase", apiBase), [apiBase]);
  return { apiBase, setApiBase };
}

async function fetchJson(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`HTTP ${r.status}: ${text.slice(0, 300)}`);
  }
  return r.json();
}

// ---------- UI primitives (Tailwind) ----------
function Input({ className = "", ...props }) {
  return <input className={`w-full rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 ${className}`} {...props} />
}
function Button({ className = "", variant = "primary", ...props }) {
  const base = "inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition";
  const styles = variant === "ghost" ? "bg-transparent hover:bg-zinc-800 text-zinc-200" :
                 variant === "secondary" ? "bg-zinc-800 hover:bg-zinc-700 text-zinc-100" :
                 "bg-indigo-600 hover:bg-indigo-500 text-white";
  return <button className={`${base} ${styles} ${className}`} {...props} />
}
function Chip({ children }) {
  return <span className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs text-zinc-300">{children}</span>;
}
function Card({ children, className = "" }) {
  return <div className={`rounded-2xl border border-zinc-800 bg-zinc-900/60 shadow-sm ${className}`}>{children}</div>;
}

// ---------- Layout ----------
function Shell({ children, apiBase, setApiBase }) {
  const [showCfg, setShowCfg] = useState(false);
  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-950 to-zinc-900 text-zinc-100">
      <header className="sticky top-0 z-20 border-b border-zinc-800/70 bg-zinc-950/80 backdrop-blur supports-[backdrop-filter]:bg-zinc-950/60">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <nav className="flex items-center gap-3 text-sm">
            <Link className="rounded-xl px-2 py-1 hover:bg-zinc-800" to="/">Home</Link>
            <Link className="rounded-xl px-2 py-1 hover:bg-zinc-800" to="/browse">Browse</Link>
            <Link className="rounded-xl px-2 py-1 hover:bg-zinc-800" to="/trending">Trending</Link>
            <Link className="rounded-xl px-2 py-1 hover:bg-zinc-800" to="/top-rated">Top Rated</Link>
            <Link className="rounded-xl px-2 py-1 hover:bg-zinc-800" to="/recs">Recs</Link>
          </nav>
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => setShowCfg(v => !v)}>API</Button>
          </div>
        </div>
        {showCfg && (
          <div className="mx-auto max-w-6xl px-4 pb-3">
            <div className="flex items-center gap-2">
              <label className="text-xs text-zinc-400">API Base</label>
              <Input value={apiBase} onChange={e => setApiBase(e.target.value)} />
              <Button onClick={() => setShowCfg(false)}>Close</Button>
            </div>
            <p className="mt-1 text-xs text-zinc-500">e.g. http://127.0.0.1:8000/api</p>
          </div>
        )}
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        {children}
      </main>
      <footer className="mx-auto max-w-6xl px-4 py-8 text-center text-xs text-zinc-500">Movie Recommender • React + Django</footer>
    </div>
  );
}

// ---------- Pages ----------
function Home() {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card className="p-6">
        <h2 className="mb-2 text-xl font-semibold">Welcome</h2>
        <p className="text-sm text-zinc-400">Use Browse to filter the catalog, open a movie for details, or try Trending/Top Rated. Set your API base via the API button.</p>
      </Card>
      <Card className="p-6">
        <h3 className="mb-2 text-lg font-semibold">Quick Links</h3>
        <div className="flex flex-wrap gap-2">
          <Link to="/browse"><Button>Browse</Button></Link>
          <Link to="/trending"><Button variant="secondary">Trending</Button></Link>
          <Link to="/top-rated"><Button variant="secondary">Top Rated</Button></Link>
          <Link to="/recs"><Button variant="ghost">Recommendations</Button></Link>
        </div>
      </Card>
    </div>
  );
}

function Browse({ apiBase }) {
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
    <div className="grid gap-4">
      <Card className="p-4">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-6">
          <div className="col-span-2 md:col-span-2">
            <label className="mb-1 block text-xs text-zinc-400">Title</label>
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
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
            {results.map((m) => (
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
        </>
      )}
    </div>
  );
}

function MovieDetail({ apiBase }) {
  const { slug } = useParams();
  const [state, setState] = useState({ loading: true, error: null, movie: null });
  const [mlt, setMlt] = useState({ loading: true, error: null, items: [] });

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

function SimpleList({ apiBase, title, path }) {
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

function Recs({ apiBase }) {
  const [username, setUsername] = useState("u1");
  const [state, setState] = useState({ loading: false, error: null, items: [] });

  const load = async () => {
    setState({ loading: true, error: null, items: [] });
    try {
      const data = await fetchJson(`${apiBase}/rec-cache/${encodeURIComponent(username)}/`);
      setState({ loading: false, error: null, items: data });
    } catch (e) {
      setState({ loading: false, error: e.message, items: [] });
    }
  };

  useEffect(() => { /* no auto load */ }, []);

  return (
    <div className="grid gap-4">
      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <label className="mb-1 block text-xs text-zinc-400">Username</label>
            <Input value={username} onChange={e => setUsername(e.target.value)} placeholder="e.g. u123" />
          </div>
          <Button onClick={load}>Load</Button>
        </div>
      </Card>
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
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

// ---------- App ----------
export default function App() {
  const { apiBase, setApiBase } = useApiBase();
  return (
    <BrowserRouter>
      <Shell apiBase={apiBase} setApiBase={setApiBase}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/browse" element={<Browse apiBase={apiBase} />} />
          <Route path="/movie/:slug" element={<MovieDetail apiBase={apiBase} />} />
          <Route path="/trending" element={<SimpleList apiBase={apiBase} title="Trending" path="/trending/" />} />
          <Route path="/top-rated" element={<SimpleList apiBase={apiBase} title="Top Rated" path="/top-rated/" />} />
          <Route path="/recs" element={<Recs apiBase={apiBase} />} />
          <Route path="*" element={<div className='text-sm text-zinc-400'>Not found</div>} />
        </Routes>
      </Shell>
    </BrowserRouter>
  );
}

// Tailwind utility classes assume Tailwind is available in the environment.
// If not, you can swap classes for plain CSS quickly.
