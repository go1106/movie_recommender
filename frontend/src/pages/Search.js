import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useApiBase, apiUrl, fetchJson } from "../lib/api";

/**
 * pages/AllMovies.jsx
 * Robust "show all films" page with search + server pagination.
 * Works with DRF-style endpoints returning either:
 *   - { results: [...], page, total_pages }  (paginated)
 *   - [...]                                    (plain array)
 * Query params supported: q, page, page_size, sort OR ordering (DRF).
 */

const PAGE_SIZES = [12, 24, 36, 48];

function cx(...xs) { return xs.filter(Boolean).join(" "); }

function MovieCard({ m }) {
  const id = m.id ?? m.slug ?? m.tmdb_id ?? m.pk ?? m.imdb_id ?? m.title;
  return (
    <Link to={`/movies/${id}`} className="group block overflow-hidden rounded-2xl border bg-white text-left">
      <div className="relative h-56 w-full bg-gray-100">
        {m.poster_url ? (
          <img
            src={m.poster_url}
            alt={`${m.title || "Movie"} poster`}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-gray-400">No Image</div>
        )}
      </div>
      <div className="space-y-1 p-3">
        <div className="flex items-center justify-between gap-2">
          <h3 className="line-clamp-1 text-sm font-semibold">{m.title || "Untitled"}</h3>
          <span className="shrink-0 text-xs text-gray-500">{m.year ?? "—"}</span>
        </div>
        {m.average_rating != null && (
          <div className="text-xs text-gray-600">Rating: {Number(m.average_rating).toFixed(1)}/10</div>
        )}
        {Array.isArray(m.genres) && m.genres.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {m.genres.slice(0, 3).map((g) => (
              <span key={g} className="inline-flex items-center rounded-full border px-2 py-0.5 text-[11px]">
                {g}
              </span>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}

function SkeletonCard() {
  return (
    <div className="animate-pulse overflow-hidden rounded-2xl border bg-white">
      <div className="h-56 bg-gray-200" />
      <div className="space-y-2 p-3">
        <div className="h-4 w-3/4 bg-gray-200" />
        <div className="h-3 w-1/2 bg-gray-200" />
        <div className="h-3 w-full bg-gray-200" />
      </div>
    </div>
  );
}

export default function AllMovies() {
  const { apiBase } = useApiBase();
  const [params, setParams] = useSearchParams();

  // URL-driven state
  const q        = params.get("q") || "";
  const page     = Math.max(1, Number(params.get("page")) || 1);
  const pageSize = PAGE_SIZES.includes(Number(params.get("page_size"))) ? Number(params.get("page_size")) : 24;
  // If your API uses DRF ordering, prefer ordering. If you implemented `sort`, keep it.
  const ordering = params.get("ordering") || "-average_rating"; // fallback: highest rated first

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [totalPages, setTotalPages] = useState(1);

  const qKey = useMemo(() => `${apiBase}|${q}|${page}|${pageSize}|${ordering}`,[apiBase,q,page,pageSize,ordering]);

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true); setError("");
      try {
        const query = new URLSearchParams({
          page: String(page),
          page_size: String(pageSize),
          ordering,               // DRF-style. If your backend expects `sort`, add it too.
          format: "json",
          ...(q ? { q } : {}),
        });

        const url = apiUrl(apiBase, "/movies/", Object.fromEntries(query.entries()));
        const data = await fetchJson(url, { headers: { Accept: "application/json" } });

        const results = Array.isArray(data) ? data
                        : Array.isArray(data.results) ? data.results
                        : Array.isArray(data.data) ? data.data
                        : Array.isArray(data.items) ? data.items
                        : [];
        if (!ignore) {
          setItems(results);
          setTotalPages(Number(data.total_pages) || Number(data.totalPages) || Number(data.pages) || page); // best-effort
        }
      } catch (e) {
        console.error("[AllMovies]", e);
        if (!ignore) setError("Failed to load movies.");
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; };
  }, [qKey]);

  // Handlers to update URL
  const setParam = (k, v) => {
    const p = new URLSearchParams(params);
    if (v === undefined || v === null || v === "") p.delete(k); else p.set(k, String(v));
    setParams(p, { replace: false });
  };

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <header className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">All Movies</h1>
          <p className="text-sm text-gray-600">Browse the full catalog. Use search and sort to refine.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <label className="text-gray-600">Page size</label>
          <select
            className="rounded-lg border px-2 py-1"
            value={String(pageSize)}
            onChange={(e) => { setParam("page_size", e.target.value); setParam("page", 1); }}
          >
            {PAGE_SIZES.map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
          <label className="ml-3 text-gray-600">Order</label>
          <select
            className="rounded-lg border px-2 py-1"
            value={ordering}
            onChange={(e) => { setParam("ordering", e.target.value); setParam("page", 1); }}
          >
            <option value="-average_rating">Rating ↓</option>
            <option value="average_rating">Rating ↑</option>
            <option value="-year">Year ↓</option>
            <option value="year">Year ↑</option>
            <option value="-created_at">Newest ↓</option>
            <option value="created_at">Oldest ↑</option>
          </select>
        </div>
      </header>

      {/* Search bar */}
      <div className="mb-4">
        <form onSubmit={(e) => { e.preventDefault(); setParam("page", 1); }} className="flex overflow-hidden rounded-xl border bg-white">
          <input
            className="w-full px-3 py-2 outline-none"
            placeholder="Search by title…"
            value={q}
            onChange={(e) => setParam("q", e.target.value)}
          />
          <button type="submit" className="px-4 font-medium">Search</button>
        </form>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {loading && items.length === 0 ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 12 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border p-6 text-center text-gray-600">No movies found.</div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {items.map((m, i) => <MovieCard key={(m.id ?? m.slug ?? i) + "_card"} m={m} />)}
        </div>
      )}

      {/* Pagination */}
      <div className="mt-6 flex items-center justify-center gap-2">
        <button
          className="rounded-xl border px-3 py-1 disabled:opacity-50"
          onClick={() => setParam("page", Math.max(1, page - 1))}
          disabled={page <= 1 || loading}
        >
          Prev
        </button>
        <span className="text-sm text-gray-600">Page {page}{totalPages ? ` / ${totalPages}` : ""}</span>
        <button
          className="rounded-xl border px-3 py-1 disabled:opacity-50"
          onClick={() => setParam("page", page + 1)}
          disabled={loading || (totalPages && page >= totalPages)}
        >
          Next
        </button>
      </div>

      <footer className="mt-10 flex items-center justify-between border-t pt-4 text-xs text-gray-500">
        <span>© {new Date().getFullYear()} Movie App</span>
        <span>Route: /movies</span>
      </footer>
    </main>
  );
}
