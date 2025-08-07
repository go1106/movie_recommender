import React, { useState, useMemo, useEffect, useCallback } from 'react';
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

  //sort and filter states
  const [sortBy, setSortBy] = useState('title'); // Default sort
  const [sortOrder, setSortOrder] = useState('asc'); // Default order       
  const [filterBy, setFilterBy] = useState('ALL'); // Default filter  
  const [minRating, setMinRating] = useState(0); // Default filter value
    


    //const dirPrefix =sortOrder === 'asc' ? '' : '-';
    //const ordering = `${dirPrefix}${sortBy}`; // Prefix for descending order

    //const fetchUrl = `http://localhost:8000/api/movies/` + `?search=${encodeURIComponent(searchTerm)}`+`&ordering=${encodeURIComponent(ordering)}`; // Construct URL with search and ordering    

    // Debounced fetch function to avoid excessive API calls
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
    const dir   = sortOrder === 'asc' ? '' : '-';
    //const ordering = `${dir}${sortBy}`; // Prefix for descending order
    const params = new URLSearchParams({
      search: searchTerm,
      ordering: dir + sortBy, // Use the dir prefix for sorting
      //filter: filterBy, // Add filter if needed
      min_rating: minRating,
    });
    const fetchUrl = `http://localhost:8000/api/movies/?${params.toString()}`; // Construct URL with search and ordering
    //const fetchUrl = `http://localhost:8000/api/movies/?search=${encodeURIComponent(searchTerm)}`;
    //console.log('Fetching URL:', fetchUrl);
    debouncedFetch(fetchUrl);
    return () => debouncedFetch.cancel();
  }, [searchTerm, sortBy, sortOrder, filterBy, minRating,debouncedFetch]);

  //extract all genres from movies 
    const allGenres = useMemo(() => {
        const genresSet = new Set();
        movies.forEach(movie => {
        if (movie.genres) {
            movie.genres.split('|').forEach(genre => genresSet.add(genre.trim()));
        }
        });
        return Array.from(genresSet);
    }, [movies]);

    // Filter movies based on search term, sort, and filter criteria

    const filteredMovies = useMemo(() => {  
        return movies
        .filter(movie => {
            const matchesSearch = movie.title.toLowerCase().includes(searchTerm.toLowerCase());
            const matchesGenre = filterBy === 'ALL' || (movie.genres && movie.genres.includes(filterBy));
            const matchesRating = movie.average_rating >= minRating;
            return matchesSearch && matchesGenre && matchesRating;
        }
        )
        
}, [movies,filterBy, minRating]);

  const [currentPage, setCurrentPage] = useState(1);
  //const [genreFilter, setGenreFilter]   = useState('All');
  const moviesPerPage = 20;

  const pageCount = Math.ceil(filteredMovies.length / moviesPerPage);
  const startIdx  = (currentPage - 1) * moviesPerPage;
  //const endIdx    = startIdx + moviesPerPage;

  // 3) Then, slice out only the current page’s items
  const paginated =filteredMovies.slice(startIdx, startIdx + moviesPerPage);
        
   


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
      {/*search*/}
      <input
        type="text"
        aria-label="Search movies"
        placeholder="Search movies..."
        value={searchTerm}
        onChange={e => setSearchTerm(e.target.value)}
        style={styles.input}
      />
        {/*sort and filter*/}
        <div>
        <label> Sort by: </label>
        <select value={sortBy} onChange={e => setSortBy(e.target.value)}>
          <option value="title">Title</option>
          <option value="average_rating">Rating</option>
          <option value="year">Year</option>
        </select>
        <select value={sortOrder} onChange={e => setSortOrder(e.target.value)}>
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>
        </div>
        {/*genre buttons*/}
        <div>   
        <label>Filter by Genre: </label>
        <select value={filterBy} onChange={e => setFilterBy(e.target.value)}>
          <option value="ALL">All</option>
          {allGenres.map(genre => (
            <option key={genre} value={genre}>
              {genre}
            </option>
          ))}
        </select>
        </div>

        {/*rating filter*/}
        <div>
        <label>Minimum Rating: </label>
        <input
          type="number"
          value={minRating}
          onChange={e => setMinRating(Number(e.target.value))}
          min="0"
          max="10"
          step="0.1"
          style={{ width: '100px', marginLeft: '10px' }}
        />
        </div>  

      {loading && <p>Loading…</p>}
      {error   && <p style={{ color: 'red' }}>Error: {error.message}</p>}
      {!loading && !movies.length && <p>No movies found.</p>}

      <ul style={styles.list}>
        {filteredMovies.map(movie => (
          <li key={movie.movieId} style={{marginBottom: '10px', border: '1px solid #ccc', padding: '10px'}}>
            <strong>{movie.title}</strong> <br />
            <span>{movie.genres}</span> <br />
            <span>Year: {movie.year || 'N/A'}</span> <br />  
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