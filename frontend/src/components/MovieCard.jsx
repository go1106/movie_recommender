// src/components/MovieCard.jsx
import { useEffect } from "react";
import { logImpression, logClick } from "../telemetry";

export default function MovieCard({ movie, lane, slot, userId }) {
  useEffect(() => {
    if (movie?.movieId) logImpression(userId, movie.movieId, { lane, slot });
  }, [movie?.movieId, lane, slot, userId]);

  const onClick = () => {
    logClick(userId, movie.movieId, { lane, slot });
    window.location.href = `/movie/${movie.slug}`;
  };

  return (
    <button onClick={onClick} className="text-left rounded-2xl shadow hover:shadow-md transition p-2">
      <img
        src={movie.poster_url || "/placeholder-poster.jpg"}
        alt={`${movie.title} poster`}
        className="w-full aspect-[2/3] object-cover rounded-xl mb-2"
        loading="lazy"
      />
      <div className="font-semibold truncate">{movie.title}</div>
      <div className="text-sm text-neutral-600">
        {movie.year ?? ""} • ⭐ {movie.average_rating?.toFixed?.(1) ?? "—"} ({movie.rating_count ?? 0})
      </div>
      {!!movie.genres?.length && (
        <div className="mt-1 flex flex-wrap gap-1">
          {movie.genres.slice(0,2).map(g => (
            <span key={g.id} className="text-xs px-2 py-0.5 bg-neutral-100 rounded-full">{g.name}</span>
          ))}
        </div>
      )}
    </button>
  );
}
