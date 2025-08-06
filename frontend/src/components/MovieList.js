import React, { useState, useMemo, useEffect } from 'react';
import debounce from 'lodash/debounce';
import axios from 'axios';

export default function MovieList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [movies, setMovies]       = useState([]);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);

    // pagination urls
  const [nextUrl, setNextUrl] = useState(null);
  const [prevUrl, setPrevUrl] = useState(null);

  const debouncedFetch = useMemo(
    () =>
      debounce((fetchUrl) => {
        setLoading(true);
        setError(null);
        axios
          .get(fetchUrl)    //.get(`http://localhost:8000/api/movies/?search=${term}`)
          .then(res => {
            setMovies(res.data.results || []); // Handle paginated results
            setNextUrl(res.data.next);
            setPrevUrl(res.data.previous);
        })
          .catch(err => setError(err))
          .finally(() => setLoading(false));
      }, 300),
    []
  );

  useEffect(() => {
    const fetchUrl = `http://localhost:8000/api/movies/?search=${encodeURIComponent(searchTerm)}`;
    debouncedFetch(fetchUrl);
    return () => debouncedFetch.cancel();
  }, [searchTerm, debouncedFetch]);


  // Handlers that reference the stateful nextUrl/prevUrl
  const handleNext = () => {
    if (nextUrl) debouncedFetch(nextUrl);
  };

  const handlePrev = () => {
    if (prevUrl) debouncedFetch(prevUrl);
  };

  

  const styles = {
    container: { padding: '20px' },
    input:     { marginBottom: 20, padding: 10, width: '100%' },
    list:      { listStyle: 'none', padding: 0 },
    item:      { border: '1px solid #ccc', padding: 10, marginBottom: 10 },
  };

  return (
    <section style={styles.container}>
      <h2>Movie List</h2>
      <input
        type="text"
        aria-label="Search movies"
        placeholder="Search movies..."
        value={searchTerm}
        onChange={e => setSearchTerm(e.target.value)}
        style={styles.input}
      />

      {loading && <p>Loading…</p>}
      {error   && <p style={{ color: 'red' }}>Error: {error.message}</p>}
      {!loading && !movies.length && <p>No movies found.</p>}

      <ul style={styles.list}>
        {movies.map(movie => (
          <li key={movie.movieId} style={{marginBottom: '10px', border: '1px solid #ccc', padding: '10px'}}>
            <strong>{movie.title}</strong> <br />
            <span>{movie.genres}</span> <br />  
            <span>Rating: {movie.average_rating||'N/A'}</span> <br />   
          </li>
        ))}
        
      </ul>

    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button onClick={handlePrev} disabled={!prevUrl || loading}>
          ← Previous
        </button>
        <button onClick={handleNext} disabled={!nextUrl || loading}>
          Next →
        </button>
    </div>
    </section>
  );
}