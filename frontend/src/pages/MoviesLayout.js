import {Outlet, Link} from 'react-router-dom';
import React from 'react';
export default function MoviesLayout() {
  return (
    <div>
        <h1>Movies</h1>
      <nav>
        <Link to="/movies">ALLMovies</Link>
        |<Link to="/new">Add New</Link>
      </nav>
      <Outlet />
    </div>
  );
}