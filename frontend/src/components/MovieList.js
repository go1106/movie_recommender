import React, { useEffect, useState } from 'react';
import axios from 'axios';

const MovieList = () => {
  const [movies, setMovies] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:8000/api/movies/')  // Update if your backend runs at a different URL
      .then(response => {
        setMovies(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching movies:", error);
        setLoading(false);
      });
  }, []);
  const filteredMovies = movies.filter(movie =>
    movie.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style ={{ padding: '20px' }}>
      <h2>Movie List</h2>
        {loading ? (<p>Loading movies...</p> ) : (
        <>
        <input
            type="text"
            placeholder="Search movies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ marginBottom: '20px', padding: '10px', width: '100%' }} />

      <ul style ={{ padding: '0', listStyleType: 'none' }}>
        {filteredMovies.map(movie => (
          <li key={movie.movieId} style={{marginBottom: '10px', border: '1px solid #ccc', padding: '10px'}}>
            <strong>{movie.title}</strong> <br />
            <span>{movie.genres}</span> <br />  
            <span>Rating: {movie.average_rating||'N/A'}</span> <br />   
          </li>
        ))}
      </ul>
      </> 
        )}
      <p>Total Movies: {filteredMovies.length}</p>
    </div>
  );
};

export default MovieList;
