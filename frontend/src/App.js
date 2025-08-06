import React from 'react';
import MovieList from './components/MovieList';
//import RatingList from './components/RatingList';
//import { BrowserRouter as Router, Routes,Route } from 'react-router-dom';



function App() {
  return (
    <div className="App">
      <h1>Movie Recommender</h1>
      <MovieList/>
    </div>
  );
    
}

export default App;
