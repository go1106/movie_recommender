// src/pages/MovieDetail.jsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet } from "../api";
import MovieCard from "../components/MovieCard";
import ProvidersBar from "../components/ProvidersBar";

export default function MovieDetail({ userId }) {
  const { slug } = useParams();
  const [movie, setMovie] = useState(null);
  const [more, setMore] = useState([]);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let current = true;
    (async () => {
      try {
        const m = await apiGet(`/api/movies/${slug}/`);
        if (!current) return;
        setMovie(m);
        const ml = await apiGet(`/api/movies/${m.movieId}/more-like-this/`, { k: 12 });
        if (!current) return;
        setMore(ml);
      } catch (e) {
        if (current) setErr(e);
      }
    })();
    return () => { current = false; };
  }, [slug]);

  if (err) return <div className="text-red-600">Failed to load movie</div>;
  if (!movie) return <div className="h-96 animate-pulse bg-neutral-100 rounded-2xl" />;

  return (
    <div className="space-y-8">
      <header className="flex flex-col md:flex-row gap-6">
        <img src={movie.poster_url || "/placeholder-poster.jpg"} alt={`${movie.title} poster`} className="w-48 rounded-xl" />
        <div className="flex-1">
          <h1 className="text-3xl font-bold">
            {movie.title} <span className="text-neutral-500">({movie.year || "—"})</span>
          </h1>
          <div className="mt-2 text-sm text-neutral-700">
            ⭐ {movie.average_rating?.toFixed?.(1) ?? "—"} • {movie.rating_count ?? 0} ratings
          </div>
          <div className="mt-4 leading-7">{movie.overview}</div>
          {!!movie.genres?.length && (
            <div className="mt-3 flex flex-wrap gap-2">
              {movie.genres.map(g => (
                <span key={g.id} className="text-xs px-2 py-0.5 bg-neutral-100 rounded-full">{g.name}</span>
              ))}
            </div>
          )}

          {/* Where to watch */}
          <ProvidersBar providers={movie.providers} region="US" />

          {/* Top billed cast */}
          {!!movie.cast?.length && (
            <div className="mt-5">
              <h3 className="font-semibold mb-2">Top billed cast</h3>
              <div className="flex gap-3 overflow-x-auto pb-2">
                {movie.cast.slice(0, 10).map(p => (
                  <div key={p.id} className="min-w-[96px] text-center">
                    <img src={p.profile_url || "/avatar.png"} alt={p.name} className="w-24 h-24 object-cover rounded-full mb-1" loading="lazy" />
                    <div className="text-xs">{p.name}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </header>

      <section>
        <h2 className="text-xl font-bold mb-3">More like this</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-3">
          {more.map((m, i) => (
            <MovieCard key={m.movieId} movie={m} lane="mlt" slot={i} userId={userId} />
          ))}
        </div>
      </section>
    </div>
  );
}
