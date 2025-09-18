import {BrowserRouter, Route, Routes, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import Browse from "./pages/Browse";
import SimpleList from "./pages/SimpleList";
import Recs from "./pages/Recs";
import MovieDetail from "./pages/MovieDetails";
import MoviesBasic from "./pages/MovieBasic";
//import Recommend from "./pages/Recommend";
import { useApiBase } from "./lib/api";
import Shell from "./components/Shell";



import "./App.css";

export default function App() {
  const { apiBase, setApiBase } = useApiBase();
  return (
    <BrowserRouter>
      
      <Shell apiBase={apiBase} setApiBase={setApiBase} variant="dark" shellClassName="!bg-black !text-white" mainClassName="!bg-black" >
        <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/browse" element={<Browse apiBase={apiBase} />} />

            <Route path="/trending" element={<SimpleList apiBase={apiBase} title="Trending" path="/trending/" />} />
            <Route path="/top-rated" element={<SimpleList apiBase={apiBase} title="Top Rated" path="/top-rated/" />} />
            <Route path="/recs" element={<Recs apiBase={apiBase} />} />
            <Route path="/movie/:slug" element={<MovieDetail apiBase={apiBase} />} />
            <Route path="*" element={<div>404 Not Found</div>} />
        </Routes>
      </Shell>
      <footer className="mx-auto max-w-6xl px-4 py-8 text-center text-xs text-zinc-500">Movie Recommender • React + Django</footer>
    </BrowserRouter>
  );
}
