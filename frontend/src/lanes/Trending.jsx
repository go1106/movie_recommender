// src/lanes/Trending.jsx
import { useEffect, useState } from "react";
import { apiGet } from "../api";
import MovieCard from "../components/MovieCard";

export default function Trending({ userId }) {
  const [items, setItems] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    apiGet("/api/trending/", { days: 7 })
      .then(setItems)
      .catch(setErr);
  }, []);

  if (err) return <div className="text-red-600">Failed to load trending</div>;
  if (!items) return <SkeletonRow />;

  return (
    <section className="my-6">
      <h2 className="text-xl font-bold mb-3">Trending now</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-3">
        {items.map((m, i) => (
          <MovieCard key={m.movieId} movie={m} lane="trending" slot={i} userId={userId} />
        ))}
      </div>
    </section>
  );
}

function SkeletonRow() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-3">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="rounded-2xl bg-neutral-100 animate-pulse h-64" />
      ))}
    </div>
  );
}
