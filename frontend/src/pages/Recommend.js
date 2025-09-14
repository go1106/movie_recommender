import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

/**
 * HomePage.jsx
 * Landing page redesigned per spec:
 * - Top-left: Sign in button
 * - Nav includes a Home link and a link group: Add New Movie, Add Comment, Add Tag, Rating
 * - Center: search bar
 * - Bottom: links (titles) for Top 10 rated movies
 * - Background: cycle Top 10 posters one-by-one (slideshow)
 *
 * API used (adjust to your backend):
 *   GET /api/movies/?sort=rating_desc&page=1&page_size=10
 *     -> { results: [{ id, title, poster_url, year, average_rating, ... }], ... }
 */

// ---------- API client ----------


const TOP10_ENDPOINT = "/api/movies/";

export default function Recommend() {
  const navigate = useNavigate();

  // Top 10 state
  const [top, setTop] = useState([]);
  const [loadingTop, setLoadingTop] = useState(false);
  const [errorTop, setErrorTop] = useState("");

  // Background slideshow index
  const [slide, setSlide] = useState(0);
  const timerRef = useRef(null);

  // Search state
  const [query, setQuery] = useState("");

  // Fetch Top 10 rated movies
  useEffect(() => {
    let ignore = false;
    async function fetchTop() {
      setLoadingTop(true);
      setErrorTop("");
      try {
        const qs = new URLSearchParams({ sort: "rating_desc", page: "1", page_size: "10" });
        const res = await fetch(`${TOP10_ENDPOINT}?${qs.toString()}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!ignore) setTop(data.results ?? []);
      } catch (e) {
        console.error(e);
        if (!ignore) setErrorTop("Failed to load Top 10.");
      } finally {
        if (!ignore) setLoadingTop(false);
      }
    }
    fetchTop();
    return () => { ignore = true; };
  }, []);

  // Auto-advance slideshow
  useEffect(() => {
    if (!top || top.length === 0) return;
    timerRef.current = setInterval(() => {
      setSlide((i) => (i + 1) % top.length);
    }, 4000);
    return () => clearInterval(timerRef.current);
  }, [top]);

  // Submit search
  function onSearch(e) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    navigate(`/search?q=${encodeURIComponent(q)}`);
  }

  // Id helper
  function mid(m, i) { return m.id ?? m.slug ?? m.tmdb_id ?? String(i); }

  return (
    <main className="relative min-h-screen overflow-hidden">
      {/* Background slideshow */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-black/40 to-black/40 z-[1]" />
        {/* Stack all images and fade the active one in */}
        {(top?.length ? top : Array.from({ length: 1 }).map(() => ({}))).map((m, i) => (
          <img
            key={mid(m, i)}
            src={m.poster_url || ""}
            alt={m.title ? `${m.title} poster` : "background"}
            className={[
              "absolute inset-0 h-full w-full object-cover transition-opacity duration-1000",
              top?.length ? (i === slide ? "opacity-100" : "opacity-0") : "opacity-100",
            ].join(" ")}
          />
        ))}
        {/* Fallback color when no images */}
        {(!top || top.length === 0) && (
          <div className="absolute inset-0 bg-zinc-900" />
        )}
      </div>

      {/* Header / Nav */}
      <header className="relative z-10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 text-white">
          {/* Left: Sign in */}
          <div className="flex items-center gap-3">
            <Link
              to="/signin"
              className="rounded-xl bg-white/90 px-3 py-1 text-sm font-medium text-black hover:bg-white"
            >
              Sign in
            </Link>
          </div>

          {/* Center: Home link */}
          <nav className="hidden sm:block">
            <Link to="/" className="text-sm font-semibold underline underline-offset-4">
              Home
            </Link>
          </nav>

          {/* Right: Link group */}
          <nav className="flex flex-wrap items-center gap-2 text-sm">
            <Link to="/movies/create" className="rounded-xl bg-white/15 px-3 py-1 hover:bg-white/25">Add New Movie</Link>
            <Link to="/comments/create" className="rounded-xl bg-white/15 px-3 py-1 hover:bg-white/25">Add Comment</Link>
            <Link to="/tags/create" className="rounded-xl bg-white/15 px-3 py-1 hover:bg-white/25">Add Tag</Link>
            <Link to="/ratings/create" className="rounded-xl bg-white/15 px-3 py-1 hover:bg-white/25">Rating</Link>
          </nav>
        </div>
      </header>

      {/* Center search */}
      <section className="relative z-10 flex items-center justify-center px-4 py-20">
        <div className="w-full max-w-2xl">
          <h1 className="mb-4 text-center text-3xl font-extrabold tracking-tight text-white drop-shadow-sm">
            Find your next favorite movie
          </h1>
          <form onSubmit={onSearch} className="flex overflow-hidden rounded-2xl border border-white/30 bg-white/90 backdrop-blur">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search movies by title…"
              className="w-full px-4 py-3 outline-none"
              aria-label="Search movies"
            />
            <button type="submit" className="whitespace-nowrap px-5 font-medium text-white" style={{ backgroundColor: "#111" }}>
              Search
            </button>
          </form>
          {/* Hint */}
          <p className="mt-2 text-center text-xs text-white/80">Press Enter to search • Results open on the Search page</p>
        </div>
      </section>

      {/* Bottom: Top 10 links */}
      <section className="pointer-events-auto absolute inset-x-0 bottom-0 z-10">
        <div className="mx-auto max-w-7xl px-4 pb-6">
          <div className="rounded-2xl border border-white/20 bg-black/30 p-3 backdrop-blur">
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-white/80">Top 10 Rated</h2>
            {errorTop ? (
              <div className="rounded-lg border border-yellow-200 bg-yellow-50/90 p-2 text-xs text-yellow-800">{errorTop}</div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {loadingTop && top.length === 0 ? (
                  Array.from({ length: 10 }).map((_, i) => (
                    <span key={i} className="inline-flex animate-pulse rounded-full bg-white/20 px-3 py-1 text-xs text-transparent">Loading</span>
                  ))
                ) : top.length === 0 ? (
                  <span className="text-xs text-white/80">No data.</span>
                ) : (
                  top.map((m, i) => (
                    <Link
                      key={mid(m, i)}
                      to={`/movies/${mid(m, i)}`}
                      className="inline-flex rounded-full bg-white/85 px-3 py-1 text-xs font-medium text-black hover:bg-white"
                    >
                      {i + 1}. {m.title}
                    </Link>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Screen reader-only live region for background slide label */}
      <div className="sr-only" aria-live="polite">Background slide {slide + 1} of {Math.max(1, top.length)}</div>

      {/* Footer spacing so bottom bar doesn't overlap content on very small screens */}
      <div className="h-20" />
      <h1 className="text-3xl font-extrabold tracking-tight md:text-4xl">
              Discover, rate, and curate your favorite films
        </h1>
    </main>
  );
}
