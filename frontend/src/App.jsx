import {BrowserRouter, Route, Routes, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import Search from "./pages/Search";
import MoviesBasic from "./pages/MovieBasic";
//import Recommend from "./pages/Recommend";

import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <nav>
        <ul>
          <li>
            <Link to="/">Home</Link>
          </li>
          <li>
            <Link to="/about">About</Link>
          </li>
          <li>
            <Link to="/contact">Contact</Link>
          </li>
        </ul>
      </nav>
      <Routes>
        <Route path="/" element={<MoviesBasic />} />
        <Route path="/search" element={<Search />} />
        {/* <Route path="/recommend" element={<Recommend />} /> */}
        <Route path="*" element={<div>404 Not Found</div>} />
        
        
  
      </Routes>
    </BrowserRouter>
  );
}
