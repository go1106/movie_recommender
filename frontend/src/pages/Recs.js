import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchJson } from "../lib/api";
import Card from "../components/Card";
import Poster from "../components/Poster";
import Input from "../components/Input";
import Button from "../components/Button";  

export default function Recs({ apiBase }) {
  const [username, setUsername] = useState("u1");
  const [state, setState] = useState({ loading: false, error: null, items: [] });

  const load = async () => {
    setState({ loading: true, error: null, items: [] });
    try {
      const data = await fetchJson(`${apiBase}/rec-cache/${encodeURIComponent(username)}/`);
      setState({ loading: false, error: null, items: data });
    } catch (e) {
      setState({ loading: false, error: e.message, items: [] });
    }
  };

  useEffect(() => { /* no auto load */ }, []);

  return (
    <div className="grid gap-4">
      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <label className="mb-1 block text-xs text-zinc-400">Username</label>
            <Input value={username} onChange={e => setUsername(e.target.value)} placeholder="e.g. u123" />
          </div>
          <Button onClick={load}>Load</Button>
        </div>
      </Card>
      {state.loading && <Card className="p-4 text-sm text-zinc-400">Loading…</Card>}
      {state.error && <Card className="p-4 text-sm text-red-400">Error: {state.error}</Card>}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {state.items.map(m => (
          <Link key={m.id} to={`/movie/${m.slug}`} className="group">
            <Card className="overflow-hidden">
              <Poster src={m.poster_url} alt={m.title} className="h-64 w-full object-cover" />
              <div className="p-3">
                <div className="line-clamp-1 font-medium group-hover:text-indigo-400">{m.title}</div>
                <div className="mt-0.5 text-xs text-zinc-400">{m.release_year ?? "—"}</div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}