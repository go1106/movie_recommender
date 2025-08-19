// src/pages/Search.jsx
import { useEffect, useState } from "react";
import { apiGet } from "../api";
import MovieCard from "../components/MovieCard";

export default function Search({ userId }) {
  const [q, setQ] = useState("");
  const [genre, setGenre] = useState("");
  const [data, setData] = useState({ results: [], page: 1, size: 24 });

  const fetchPage = async (page = 1) => {
    const d = await apiGet("/api/movies/", { q, genre, page, size: 24 });
    setData(d);
  };

  useEffect(() => { fetchPage(1); /* eslint-disable */ }, [q, genre]);

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <input className="border rounded px-3 py-2 w-full" placeholder="Search movies…"
               value={q} onChange={e => setQ(e.target.value)} />
        <select className="border rounded px-2" value={genre} onChange={e => setGenre(e.target.value)}>
          <option value="">All genres</option>
          {/* You can fetch real genres and map here */}
          <option>Drama</option><option>Comedy</option><option>Animation</option>
        </select>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-3">
        {data.results.map((m, i) => (
          <MovieCard key={m.movieId} movie={m} lane="search" slot={i} userId={userId} />
        ))}
      </div>

      <div className="mt-4 flex justify-center gap-2">
        <button className="px-3 py-1 border rounded" disabled={data.page<=1} onClick={()=>fetchPage(data.page-1)}>Prev</button>
        <button className="px-3 py-1 border rounded" onClick={()=>fetchPage(data.page+1)}>Next</button>
      </div>
    </div>
  );
}
