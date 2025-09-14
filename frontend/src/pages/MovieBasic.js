import React, { useEffect, useState } from "react";

/**
 * MoviesBasic.jsx — Function #1 only
 * Displays basic movie data: image, name (title), and year.
 * No dependencies on your helpers; CRA-safe.
 *
 * Backend expectation:
 *   GET {API_BASE}/movies/?format=json&page=1&page_size=48
 * Returns either an array [...]
 *   or an object { results: [...], ... }
 */

// CRA-safe API base. Use a dev proxy or set REACT_APP_API_BASE=http://127.0.0.1:8000/api
const API_BASE = (process.env.REACT_APP_API_BASE || "/api").replace(/\/$/, "");
const apiUrl = (path, params) => {
  const url = `${API_BASE}/${String(path).replace(/^\//, "")}`;
  if (!params) return url;
  const qs = new URLSearchParams(params);
  return `${url}?${qs.toString()}`;
};

export default function MoviesBasic() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true); setError("");
      try {
        const url = apiUrl("/api/movies/", { format: "json", page: "1", page_size: "48" });
        const res = await fetch(url, { headers: { Accept: "application/json" }, credentials: "include" });
        const ct = res.headers.get("content-type") || "";
        const text = await res.text();
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${text.slice(0,120)}`);
        let data;
        try { data = JSON.parse(text); }
        catch { throw new Error(`Non-JSON from /movies/ (ct=${ct}). Head: ${text.slice(0,120)}`); }
        const list = Array.isArray(data) ? data
          : Array.isArray(data.results) ? data.results
          : Array.isArray(data.data) ? data.data
          : Array.isArray(data.items) ? data.items
          : [];
        if (!ignore) setItems(list);
      } catch (e) {
        console.error("[MoviesBasic]", e);
        if (!ignore) setError("Failed to load movies.");
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; };
  }, []);

  const getId = (m, i) => m.id ?? m.slug ?? m.tmdb_id ?? m.pk ?? m.imdb_id ?? String(i);
  const getTitle = (m) => m.title || m.name || "Untitled";
  const getYear = (m) => m.year ?? m.release_year ?? (m.release_date ? String(m.release_date).slice(0,4) : "—");
  const getImg = (m) => m.poster_url || m.poster || m.image_url || m.image || m.poster_path || "";

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <h1 className="mb-4 text-2xl font-bold">Movies</h1>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {loading && items.length === 0 ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="animate-pulse overflow-hidden rounded-2xl border bg-white">
              <div className="h-56 bg-gray-200" />
              <div className="space-y-2 p-3">
                <div className="h-4 w-3/4 bg-gray-200" />
                <div className="h-3 w-1/2 bg-gray-200" />
              </div>
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border p-6 text-center text-gray-600">No movies found.</div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {items.map((m, i) => (
            <div key={getId(m, i)} className="overflow-hidden rounded-2xl border bg-white">
              <div className="relative h-56 w-full bg-gray-100">
                {getImg(m) ? (
                  <img src={getImg(m)} alt={`${getTitle(m)} poster`} className="h-full w-full object-cover" loading="lazy" />
                ) : (
                  <div className="flex h-full w-full items-center justify-center text-gray-400">No Image</div>
                )}
              </div>
              <div className="p-3">
                <div className="line-clamp-1 text-sm font-semibold">{getTitle(m)}</div>
                <div className="text-xs text-gray-600">{getYear(m)}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
